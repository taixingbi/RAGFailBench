# Labeling guide: human audit v2

**Files.** Annotator 1 fills `clean_audit_annotator1.csv` (50 rows) and
`failure_audit_annotator1.csv` (54 rows); annotator 2 fills the `annotator2` copies.
Label independently: do not look at the other annotator's file, the model outputs or
any automatic verdict. Do not look anything up; judge only from the row. Label one row
at a time. Every `fix`, `reject`, `no` or non-`ok` label needs a short note saying why.
Leave a cell blank if you did not label it; never fill a column in bulk.

## Clean seeds: `decision` = keep / fix / reject

Read the question alone first, as a user with no passage would. Then read the gold
answer and the supporting sentence.

| Label | Use when | Examples |
|---|---|---|
| **keep** | The question is self-contained, has exactly one correct answer, the gold answer is that answer, and the supporting sentence states it. Long or multi-word gold answers are fine. | "When did Albert Einstein die?" → *18 April 1955* |
| **fix** | Usable after a small edit to the question or gold answer. Say the edit in `notes`. | Unresolved reference: "Where was **he** born?" · Two plausible answers: "Who founded Apple?" (*Steve Jobs*; Wozniak also) · Time-dependent: "Who is the **current** CEO…?" · Asks two things, gold answers one: "When and where…?" · Gold answer incomplete or over-long |
| **reject** | No small edit rescues it: the sentence does not support the answer, the gold answer is wrong, the question is trivial or nonsensical, or it only asks what the title is. | Gold not in or contradicted by the sentence · "What is a sunset provision?" |

Per-row checks (`yes` / `no`):

- `question_clear`: a reader who has not seen the passage understands what is asked.
- `answer_in_evidence`: the supporting sentence states the gold answer.
- `answer_unique`: there is one correct answer, and the gold answer is it.
- `needs_title`: `yes` if the question only makes sense once you know the page title.
- `time_sensitive_ok`: `yes` if the answer will not change over time.

`decision` is `keep` only if `question_clear`, `answer_in_evidence`, `answer_unique` and
`time_sensitive_ok` are all `yes` and `needs_title` is `no`.

## Failure cases

`operator_claim` says what the operator is supposed to have done; `contexts` are the
passages, separated by `---`. Check the claim against the passages.

- `human_injection_valid` (`yes` / `no`): the passages do what the claim says.
- `human_label_correct` (`yes` / `no`): `answer_available` is right. `False` means the
  gold answer cannot be found or inferred from the passages; `True` means it can.
- `severity_ok` (`yes` / `no` / `unclear`): the case matches its severity (below).
- `issue_code`: `ok`, or the main problem: `answer_leaked` (abstain case, but the answer
  can be found), `distractor_supports_answer`, `midword_split`, `too_easy`,
  `empty_or_broken_context`, `position_not_matched_budget`, `other` (explain in notes).

| Operator | low | medium | high | Typical failures to look for |
|---|---|---|---|---|
| missing_evidence | only passages from other pages | neighbouring passages of the same page | the gold passage with the answer sentence deleted | answer still stated or inferable elsewhere → `answer_leaked` |
| hard_negative | 2 topical passages | 4 topical passages | 8 topical passages | a passage states the answer → `answer_leaked` |
| conflict | gold first, conflicting copy last | conflicting copy just before gold | conflicting copy first and repeated, gold last | the two copies do not actually disagree, or the alternate is also correct |
| context_noise | 25% distractors | 50% distractors | 75% distractors | gold passage missing; a distractor supports the answer |
| chunk_boundary | sentence split into 2 adjacent pieces | 2 pieces with a distractor between | 3 pieces with distractors between | pieces cannot be recombined; split inside a word → `midword_split` |
| evidence_position | gold passage first | gold passage in the middle | gold passage last | gold passage missing or not where the severity says |

## After labeling

Save the CSVs unchanged in structure and tell Claude. The audit statistics (HAR with a
95% Wilson CI, failure validity per operator, Cohen's κ between annotators) are
computed from these files only. `manifest.json` maps each `audit_id` back to its run
and holds the hidden automatic verdicts for comparison afterwards.
