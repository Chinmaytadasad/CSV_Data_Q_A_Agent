# Computation Approach & Anti-Hallucination Design

## Core Principle
This agent never lets the LLM state an answer in prose. The model's only job is to write pandas code; the answer shown to the user always comes from *executing* that code against the real DataFrame, never from the model's own claims about what the data contains. If the model hallucinates a wrong number in its reasoning, it has no way to surface that hallucination as the final answer — only the executed `result` variable is ever displayed.

## Three-Layer Safety Design

**1. Structural constraint on the model's output**
The system prompt (`prompt_builder.py`) restricts the model to emitting only raw pandas code, with a hard requirement that the final line assigns to a variable named `result`. No prose, no explanations, no markdown fences are permitted. This removes any surface area for the model to state a conclusion outside of code — there is no "answer" field it can fill in directly.

**2. Execution-only truth**
`executor.py` runs the generated code in a namespace pre-loaded with `pd` and a copy of the DataFrame, then reads `result` back out of that same namespace after execution. The displayed answer is never parsed from the model's text response — it is read from a live Python variable that only exists if the code actually ran. If `result` isn't present after execution, the agent raises an error rather than silently returning nothing.

**3. Sandboxing**
`sanitize()` blocklists `import`, `exec`, `eval`, `__`, `open(`, `os.`, `sys.`, and `subprocess` before any code reaches `exec()`. This is a reasonable safeguard for a 24-hour assessment context, not production-grade isolation — there is no subprocess or container boundary, so a sufficiently obfuscated payload could in principle bypass a string-based blocklist. A production version would run generated code in a separate process or container with resource limits, rather than in-process `exec()`.

## Retry / Repair Loop
If the generated code fails (syntax error, missing column, runtime exception), the failure is fed back to the model along with the original code and the traceback, and one repair attempt is made. If the repair also fails, the agent returns a clear failure state (`success=False`, populated `error_note`) rather than a misleading partial result.

## Known Limitations (found during testing)

**1. Silent-failure risk from mismatched exec namespaces (fixed).** Early in development, `execute()` used separate globals/locals dictionaries in `exec()`. Assignments made by generated code landed in the locals dict, not the one being read back, so `result` was silently `None` even when the generated code was correct. Fixed by using a single namespace dict as both globals and locals, plus an explicit check that raises if `result` is never assigned.

**2. Prompt sensitivity in refusal logic.** An early version of the UNANSWERABLE guard (added to stop the agent from hallucinating full-table dumps in response to garbled or off-topic input) was too broad and incorrectly refused legitimate boolean/existence questions like "are there any sales in Q2?". Tightening the instruction with explicit criteria and a worked example fixed the observed cases, but this remains a soft, prompt-based classification rather than a hard rule, so edge cases may still be misclassified in either direction.

**3. Output structure depends on question phrasing.** A vague multi-part question ("what were the highest revenue and sales in q1, q2, q3, give them separately") produced a flat, unlabeled list where it was unclear which value corresponded to which quarter or metric. Rephrasing the same underlying question with more explicit structure ("...in a table wise") produced a correctly labeled DataFrame. The model can produce well-structured output, but the current prompt doesn't reliably push it toward that shape for ambiguous phrasing. A more robust version would post-process the prompt to detect multi-part questions and explicitly instruct the model to return a labeled DataFrame or dict in those cases.

**4. Inconsistent handling of "not found" entities.** Filtering on a region that doesn't exist ("What was revenue in the Central region?") returned a defensible `0.0` (empty filter summed to zero). Filtering on a product framed as "the nonexistent entity Zeta" instead triggered the UNANSWERABLE path. Both are reasonable individually, but the behavior is phrasing-dependent rather than logic-dependent — the word "nonexistent" in the question likely nudges the model toward refusal, while a plain filter on a fictional value does not. A more consistent design would always attempt the filter and report zero/empty results rather than pattern-matching on words like "nonexistent" or "does not exist."

**5. Non-deterministic handling of compound questions.** The same compound-question shape ("total revenue for East in Q2 and average units_sold for Alpha products") was rejected as UNANSWERABLE ("multiple unrelated questions") in one run and answered correctly with a tuple in another, using identical code and prompt. Temperature is set low (0.1) but not zero, so generation is not fully deterministic for boundary-case classification. A production version would likely separate the "is this answerable" decision into its own deterministic (temperature=0, or rule-based) classification step, rather than folding it into the same generation call that produces the code.

**6. Independent column-max semantics for paired questions.** For questions like "highest revenue and sales per quarter," the implementation computes `.groupby('quarter')[['revenue', 'units_sold']].max()`, which takes the column-wise maximum independently within each group. This is standard pandas behavior and produces correct numbers, but the two values in a given row are not guaranteed to come from the same underlying transaction, which could be visually misread as a single co-occurring event.

**7. No output truncation for accidental non-command input.** Early testing showed that a mistyped exit command (e.g. "uit" instead of "quit") was not recognized as an exit and was forwarded to the LLM as a genuine question, which produced a full unfiltered dump of the dataset with derived columns. This surfaced a broader point: any unrecognized input falls through to the LLM rather than being validated first, which is by design (keeps the agent flexible) but means malformed input can produce large, unhelpful output rather than a clean rejection.

**8. Schema context hid the real value type of `object`-dtype columns (found, root-caused, and fixed).** Tested against a real-world Kaggle retail dataset (not just the bundled synthetic data), the question "How many transactions had a discount applied?" returned `0` — silently wrong, with no error at any stage. Root cause: the `Discount Applied` column loads as `object` dtype, but its actual non-null values are Python `bool` (`True`/`False`), not strings. The schema context reported only the dtype label `object`, giving the model no signal that the values inside were booleans rather than strings; it reasonably generated `df['Discount Applied'].eq('True')`, comparing a real `True` against the string `'True'`, which is never equal — silently returning 0 for every row. Both sanitization and execution succeeded, so nothing in the pipeline flagged this as a failure; it was a logically wrong answer presented with full confidence.

This is the clearest evidence in this project that "the code executed successfully" is a necessary but not sufficient guarantee of correctness — execution-only truth prevents the model from *stating* a wrong number, but doesn't prevent it from *computing* one if it misjudges what a column actually contains.

**Fix:** `build_schema_context()` was updated to sample the actual Python types of non-null values within `object`-dtype columns, and report that instead of the bare dtype label — e.g. `"object (boolean values: True/False, use == True/False, not string comparison)"` rather than just `"object"`. After the fix, the same question generated `df['Discount Applied'].sum()` (a valid boolean-sum idiom) and returned the correct answer, `4219`, verified against a direct `(df['Discount Applied'] == True).sum()` check. The fix was regression-tested against the original synthetic dataset with no change in behavior for existing questions.

## What I'd Improve With More Time
- Separate the "answerable vs. not" classification into a deterministic step, independent of code generation
- Post-process multi-part questions to explicitly request structured (labeled DataFrame/dict) output
- Replace the string-blocklist sandbox with real process/container isolation
- Standardize not-found-entity handling to always attempt the filter rather than refuse based on question phrasing
- Add automated regression tests covering the specific edge cases found during manual testing (namespace bug, UNANSWERABLE over-triggering, compound-question non-determinism)
- Extend the object-column type-sampling approach (added for booleans) to also flag numeric-looking strings, mixed date formats, and other common real-world dtype mismatches beyond the one case found here