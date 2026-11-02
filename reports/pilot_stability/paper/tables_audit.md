**Human audit summary (replaces the HAR and failure-validity rows of Table V). Blind stratified sample from the three seeded runs; 95% Wilson CIs. Annotator 1 is primary.**

| Metric | Annotator 1 | Annotator 2 |
|---|---|---|
| Human acceptance (HAR), clean seeds | 84.0% [71.5, 91.7] (42/50) | 86.0% [73.8, 93.0] (43/50) |
| Failure injection valid | 96.3% [87.5, 99.0] (52/54) | 98.1% [90.2, 99.7] (53/54) |
| Failure label (answer available) correct | 100.0% [93.4, 100.0] (54/54) | 100.0% [93.4, 100.0] (54/54) |

**Human audit per seeded run (replaces Tables VI and VIII human columns): clean seeds kept and failure cases judged valid, per annotator. Per-run samples are small (16–17 seeds, 18 failure cases); pooled values are in the summary table.**

| Run | HAR A1 | HAR A2 | Failure validity A1 | Failure validity A2 |
|---|---|---|---|---|
| pilot_stability_s42 | 16/16 | 16/16 | 17/18 | 17/18 |
| pilot_stability_s123 | 13/17 | 13/17 | 17/18 | 18/18 |
| pilot_stability_s2026 | 13/17 | 14/17 | 18/18 | 18/18 |
| All runs | 42/50 | 43/50 | 52/54 | 53/54 |

**Primary reason for the 8 of 50 audited clean seeds annotator 1 did not keep (replaces Table IX). One primary reason per row from the structured flags, in the order listed; the free-text note gives the detail.**

| Reason | Count | Percent | Structured basis | Rows |
|---|---|---|---|---|
| Time-sensitive phrasing | 2 | 25.0% | time_sensitive_ok = no | C022 (fix), C027 (fix) |
| Answer not unique | 1 | 12.5% | answer_unique = no | C002 (fix) |
| Unclear question (reference, premise, wording) | 4 | 50.0% | question_clear = no | C010 (fix), C039 (fix), C044 (fix), C047 (fix) |
| Other (trivial; see note) | 1 | 12.5% | no flag set | C040 (reject) |

**Failure-injection verification: automatic check on every case versus the human audit (replaces Table XI). Per-operator samples are 9 cases (3 per severity).**

| Check | Annotator 1 | Annotator 2 |
|---|---|---|
| Automatic structural verification (leakage / label check), all cases | 94.9% ± 0.3% pass |  |
| Human: injection valid, all operators | 96.3% [87.5, 99.0] (52/54) | 98.1% [90.2, 99.7] (53/54) |
|   missing_evidence | 9/9 | 9/9 |
|   hard_negative | 9/9 | 9/9 |
|   conflict | 7/9 | 8/9 |
|   context_noise | 9/9 | 9/9 |
|   chunk_boundary | 9/9 | 9/9 |
|   evidence_position | 9/9 | 9/9 |

**Annotator 1 vs annotator 2 on the same audit rows. Annotator 2 had seen annotator 1's labels in an earlier pass, so this is a consistency check, not inter-annotator reliability. Kappa is undefined when both used a single identical label.**

| Field | n | Agreement | Cohen's kappa |
|---|---|---|---|
| decision | 50 | 98.0% | 0.92 |
| question_clear | 50 | 98.0% | 0.85 |
| answer_in_evidence | 50 | 100.0% | undefined (one label only) |
| answer_unique | 50 | 98.0% | 0.66 |
| time_sensitive_ok | 50 | 100.0% | 1.00 |
| needs_title | 50 | 100.0% | 1.00 |
| human_injection_valid | 54 | 98.1% | 0.66 |
| human_label_correct | 54 | 100.0% | undefined (one label only) |
| severity_ok | 54 | 74.1% | 0.14 |
