# RAGFailBench: A Reproducible Framework for Controllable RAG Failure Benchmarks

> Working paper draft. Numbers from `reports/pilot_stability/` (3-seed stability + filled 200-seed reviews) and eval reports for `pilot_stability_s{42,123,2026}` (`nova-pro`, `llama`, `gpt-oss`).

## Abstract

Retrieval-augmented generation (RAG) systems fail in structured ways—missing evidence, noisy context, bad chunking, positional bias, conflicting passages, and hard negatives—yet most benchmarks report only aggregate QA accuracy on fixed datasets. We present **RAGFailBench**, an open methodology and toolchain that (1) builds validated *clean seeds* from a corpus, (2) applies typed **Failure Operators** with controllable severity under a *matched context budget*, and (3) evaluates models so performance drops can be attributed to failure type. On a frozen Wikipedia pilot (**768** filtered pages → **12,366** chunks; config target 1000 pages), three independent dataset builds (seeds 42/123/2026) yield stable automatic funnels (QA acceptance **39.2% ± 0.2%**, failure verification **97.5% ± 0.1%**) and stable human quality (clean **HAR 66.0% ± 1.8%**, stratified failure validity **96.8% ± 1.2%**). Across three Bedrock models (`nova-pro`, `llama`, `gpt-oss`), clean accuracy is ≈ 0.81–0.85; `missing_evidence` and `hard_negative` drive large drops with high abstention, while `context_noise` / `chunk_boundary` / `evidence_position` remain weak stressors; `conflict` hurts `gpt-oss` more than the other two. We release code, configs, and regenerable artifacts so others can ablate operators rather than only download a frozen question set.

**Keywords:** RAG evaluation, failure diagnosis, controllable benchmarks, reproducibility

---

## 1. Introduction

RAG pipelines couple retrieval, chunking, and generation. Failures often arise *before* the generator: evidence is missing, buried in noise, split across chunks, placed poorly in a long context, contradicted by other passages, or replaced by near-miss distractors. Existing suites (RGB, CRUD, RAGBench, and related) primarily score **end-task performance** on fixed or semi-fixed items. They rarely expose a **controllable failure taxonomy** with severity knobs and matched clean vs. failed contexts.

**Contributions.**

1. **Failure Operators** — a typed, parameterizable API that transforms clean seeds into failure cases (`missing_evidence`, `context_noise`, `chunk_boundary`, `evidence_position`, `conflict`, `hard_negative`).
2. **Matched-budget diagnosis** — clean and failed conditions share a context chunk budget so drops are not confounded by length.
3. **Regenerable toolchain** — Wikipedia → chunks → QA → validate → inject → evaluate, with multi-seed stability reporting and human-review (HAR) hooks.
4. **Pilot evidence** — stability across three seeds on a frozen M1 corpus; three-model evaluation (`nova-pro`, `llama`, `gpt-oss`) showing operator-specific degradation patterns.

**Research questions.**

- **RQ1:** How much do systems degrade under each Failure Operator?
- **RQ2:** Do severity / difficulty controls yield predictable degradation?
- **RQ3:** Do models differ in operator sensitivity?

---

## 2. Related Work

Prior RAG benchmarks emphasize retrieval+generation accuracy, robustness to noise, or domain suites. Closest in spirit are works that inject context corruption or measure abstention; RAGFailBench differs by treating **operators as first-class, regenerable objects** with provenance, structural verification, and paper-facing stability/HAR metrics—not a one-off static dump of questions.

---

## 3. Method

### 3.1 Pipeline

```
Corpus (Wiki) → filter/chunk (M1)
             → generate candidate QA → validate → select clean seeds (M2)
             → Failure Operators × severity (M3)
             → evaluate under clean vs failed contexts (M4)
```

**Clean seed.** A validated QA item answerable from gold evidence, with `clean_contexts` sized to the same budget as failure cases.

**Failure case.** Same question and gold answer; contexts rewritten by an operator. Labels include `answer_available` and `expected_behavior` (`answer` vs `abstain`).

**Validation (not a strict Rule→Judge→Baseline funnel).** Candidates first pass deterministic rule checks (containment, title leak, uniqueness heuristics, …). Rule-passing candidates are then **independently** assessed by an LLM answerability judge and a gold-chunk baseline-answer test (baseline does *not* wait for judge acceptance). Signals are combined into a quality score; items below `min_quality_score` are rejected; finally near-duplicates are removed among accepted items. Full per-candidate records (rules, judge, baseline, quality, reasons) are stored in `5_validated/validation_results.jsonl`.

### 3.2 Failure Operators

| Operator | Stage | Mechanism | Expected |
|----------|-------|-----------|----------|
| `missing_evidence` | evidence | Remove support / gold / leave distractors | abstain |
| `context_noise` | context | Gold + distractors at noise ratio | answer |
| `chunk_boundary` | chunking | Split supporting sentence across chunks | answer |
| `evidence_position` | context | Gold at front / middle / end | answer |
| `conflict` | context | Gold kept + contradictory alternate claim | answer (prefer gold) |
| `hard_negative` | retrieval | Topical near-misses only; gold omitted | abstain |

Severities `{low, medium, high}` map to operator-specific parameters (e.g., noise ratio, split depth, conflict prominence, number of hard negatives). Post-injection **structural verification** quarantines invalid cases (e.g., answer leakage when absence is required).

### 3.3 Evaluation protocol

For each model and condition: generate an answer from concatenated contexts; score EM / token-F1 / LLM-judge correctness; track abstention. Report **accuracy**, **abstention rate**, and **drop** \(\Delta = \mathrm{acc}_{\mathrm{clean}} - \mathrm{acc}_{\mathrm{condition}}\). Aggregate **failure robustness** over failure conditions.

### 3.4 Stability protocol

Freeze M1 once (`pilot_v1` → `pilot_stability_corpus`). Repeat M2–M3 with seeds `{42, 123, 2026}` and difficulty quotas (40/40/20) enforced at generation. Report mean ± std of funnel metrics; human **HAR** = (# `keep`) / (# reviewed clean seeds); human failure validity on stratified operator samples.

---

## 4. Experimental Setup

| Item | Setting |
|------|---------|
| Corpus (config) | 200 × 5 categories = **1000** page target |
| Corpus (realized) | **768** filtered pages → **12,366** chunks (frozen); shortfalls mainly list/`too_short` rejects in location / science_technology / organization_product |
| Candidates / seeds | **1000** candidates → **200** clean seeds per run (40 per category) |
| Context budget | 8 chunks (clean and failed) |
| Generation model | Qwen2.5-7B-Instruct (`CHAT_*`) |
| Eval models | `nova-pro`, `llama`, `gpt-oss` on shared Bedrock `EVAL_BASE_URL` + `EVAL_API_KEY` (no `EVAL_MODEL`) |
| Eval coverage | All three seeds × three models |

**Provenance note.** Pilot fetch uses live MediaWiki API (not a dated dump). Formal release should pin revisions.

---

## 5. Results

### 5.1 Pipeline stability (frozen M1, three seeds)

| Metric | mean ± std |
|--------|------------|
| Candidate QA count | 1000.0 ± 0.0 |
| Schema success | 99.8% ± 0.1% |
| QA acceptance | **39.2% ± 0.2%** |
| Clean-seed count | 200.0 ± 0.0 |
| Failure verification pass | **97.5% ± 0.1%** |
| Human acceptance (HAR) | **66.0% ± 1.8%** |
| Human failure validity | **96.8% ± 1.2%** |

| run_id | accept% | fail_pass% | HAR | fail validity |
|--------|---------|------------|-----|---------------|
| `pilot_stability_s42` | 39.3% | 97.5% | 66.5% (133/200) | 97.7% (299/306) |
| `pilot_stability_s123` | 39.2% | 97.6% | 64.0% (128/200) | 95.4% (292/306) |
| `pilot_stability_s2026` | 39.0% | 97.5% | 67.5% (135/200) | 97.4% (298/306) |

Yield at 20% is by construction (`200/1000`). Difficulty mixes are aligned across seeds (~88–91 easy / 78–80 medium / 31–32 hard). Categories are balanced at selection (40 each).

### 5.2 Validation component contribution

From existing `validation_results.jsonl` only (no re-generation / no re-judge). Across three seeds (1000 candidates each):

| Validation signal | Rejected candidates | Unique rejections | Typical reason |
|-------------------|--------------------:|------------------:|----------------|
| Rule checks | 561.7 ± 6.4 | **56.0 ± 3.0** | title leakage / containment / uniqueness |
| LLM Judge | 31.3 ± 4.7 | **9.7 ± 1.5** | unsupported / unclear / unanswerable |
| Baseline test | 40.7 ± 4.9 | **2.7 ± 1.5** | gold-chunk baseline incorrect |
| Quality threshold | 537.3 ± 4.6 | 0.0 | combined score below threshold |
| Deduplication | 2.7 ± 0.6 | 2.7 ± 0.6 | near-duplicate question or fact |

**Rejected** = candidates whose reasons include that signal (rows can overlap). **Unique** = rejected candidates whose reasons map to *only* that signal. Rules dominate volume; judge and baseline still contribute non-zero unique rejects (neither is redundant). Quality threshold almost never rejects alone—it co-occurs with failed rule/judge/baseline signals that already lower the score. Full tables: `reports/pilot_stability/validation_contribution.md`.

This is a *stage contribution* analysis, not a HAR ablation: human review covers final clean seeds only, so Rule-only / Rule+Judge HAR would need new stratified annotation.

### 5.3 Human audit

| Run | Clean HAR | Failure sample validity |
|-----|-----------|-------------------------|
| `pilot_stability_s42` | 66.5% (133/200 keep) | 97.7% (299/306; 6 operators) |
| `pilot_stability_s123` | 64.0% (128/200 keep) | 95.4% (292/306) |
| `pilot_stability_s2026` | 67.5% (135/200 keep) | 97.4% (298/306) |
| **mean ± std** | **66.0% ± 1.8%** | **96.8% ± 1.2%** |

Interpret HAR as quality of *selected* seeds, not of raw candidates. Automatic acceptance (~39%) and HAR (~66%) measure different stages: the filter is still strict; humans reject additional ambiguous / time-sensitive / non-unique items among retained seeds. HAR is stable across seeds (low std) despite the absolute rate being lower than an earlier 100-seed pilot pack.

### 5.4 Model × operator (RQ1, RQ3) — primary table `pilot_stability_s42`

Clean accuracy / robustness: nova-pro **0.825 / 0.785**, llama **0.81 / 0.804**, gpt-oss **0.84 / 0.755**.

| Condition | nova-pro acc (Δ) | llama acc (Δ) | gpt-oss acc (Δ) | nova abst | llama abst | gpt-oss abst |
|-----------|------------------|---------------|-----------------|-----------|------------|--------------|
| clean | 0.825 | 0.81 | 0.84 | — | — | — |
| missing_evidence | 0.057 (−0.77) | 0.032 (−0.78) | 0.068 (−0.77) | 0.84 | 0.89 | 0.84 |
| hard_negative | 0.032 (−0.79) | 0.045 (−0.77) | 0.057 (−0.78) | 0.92 | 0.92 | 0.91 |
| conflict | 0.792 (−0.03) | 0.788 (−0.02) | 0.629 (−0.21) | 0.07 | 0.02 | 0.25 |
| context_noise | 0.927 (+0.10) | 0.941 (+0.13) | 0.955 (+0.11) | 0.05 | 0.01 | 0.01 |
| chunk_boundary | 0.906 (+0.08) | 0.930 (+0.12) | 0.902 (+0.06) | 0.08 | 0.04 | 0.07 |
| evidence_position | 0.944 (+0.12) | 0.948 (+0.14) | 0.958 (+0.12) | 0.03 | 0.01 | 0.01 |

(Negative Δ = drop vs clean. Positive Δ on noise/boundary/position reflects cases where failed contexts remain answerable and scoring variance / judge effects can exceed clean.)

**Cross-seed clean accuracy (all three models evaluated).**

| Seed | nova-pro | llama | gpt-oss |
|------|----------|-------|---------|
| s42 | 0.825 | 0.81 | 0.84 |
| s123 | 0.835 | 0.82 | 0.85 |
| s2026 | 0.835 | 0.83 | 0.845 |

**Findings.**

- **Absence operators work:** all three models mostly abstain under `missing_evidence` / `hard_negative` (acc ≈ 0.03–0.07).
- **Conflict is model-sensitive (RQ3):** mild for nova-pro / llama (~2–3 pt drop); larger for gpt-oss (~21 pt drop, abstention ~0.25).
- **Noise / boundary / position remain weak stressors** under current severities for these models.
- **Operator ranking is largely shared**; the main cross-model divergence is conflict sensitivity.

### 5.5 RQ2 (severity / difficulty)

Severity curves and difficulty-conditioned drops: report from `failure_metrics.json` / per-severity splits (fill detailed plots in camera-ready). Difficulty quotas stabilize seed composition across runs; operator severity remains the primary controllable axis for degradation curves.

---

## 6. Limitations

- Live MediaWiki pilot ≠ pinned dump; realized corpus **768 / 1000** target pages after filtering.
- HAR ~66% indicates substantial human rejection among auto-selected seeds; single annotator, no κ yet.
- `hard_negative` uses lexical overlap, not dense retrieval scores.
- `conflict` alternates are template/rewrite-based; may be stylistically unnatural.
- Weak (or inverted) drops on noise/position may indicate operator under-stress, judge noise, or model strength.
- Single-hop Wikipedia facts; multi-hop / enterprise docs are future work.

---

## 7. Conclusion

RAGFailBench reframes RAG evaluation as **controllable failure injection + matched-budget diagnosis**. The scaled pilot shows reproducible dataset construction on a frozen corpus (automatic funnels and human HAR stable across three seeds), three-model evaluation with consistent absence-operator failures, and a clear conflict sensitivity gap for `gpt-oss`. The artifact is a regenerable generator, not a static leaderboard dump.

---

## Reproducibility

```bash
make setup && make test
make pilot && make stability-freeze   # add --overwrite when replacing corpus
make stability-run && make stability-report
make evaluate-all-s42
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s123.yaml
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s2026.yaml
make validation-contribution   # stage table from validation_results.jsonl
```

Code: https://github.com/taixingbi/RAGFailBench  
Key artifacts: `reports/pilot_stability/` (incl. `validation_contribution.md`), `reports/pilot_stability_s*/failure_metrics.json`, `reviews/pilot_stability_s*/`, `configs/stability/`.

---

## Checklist (draft → submission)

- [x] Operator taxonomy (6) + matched budget
- [x] Stability table (3 seeds, 200 clean seeds, difficulty quotas aligned)
- [x] Three-model operator table (s42: nova-pro + llama + gpt-oss)
- [x] Eval all three seeds × three models
- [x] Fill 200-seed HAR; refresh stability HAR (**66.0% ± 1.8%**)
- [x] Validation component contribution (+ unique rejections); correct Rule∥Judge/Baseline wording
- [ ] Severity curves (RQ2 figures)
- [ ] Optional: stratified HAR ablation (Rule-only / Rule+Judge samples)
- [ ] Related-work depth + baselines discussion
- [ ] Pin dump / revision for camera-ready data claim
- [ ] Inter-annotator agreement (κ) on a subset
- [ ] Optional: backfill under-quota categories toward full 1000 pages
