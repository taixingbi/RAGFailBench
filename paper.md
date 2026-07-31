# RAGFailBench: A Reproducible Framework for Controllable RAG Failure Benchmarks

> Working paper draft. Numbers from `reports/pilot_stability/` (3-seed stability + filled reviews) and `pilot_stability_s42` eval (nova-pro + llama).

## Abstract

Retrieval-augmented generation (RAG) systems fail in structured ways—missing evidence, noisy context, bad chunking, positional bias, conflicting passages, and hard negatives—yet most benchmarks report only aggregate QA accuracy on fixed datasets. We present **RAGFailBench**, an open methodology and toolchain that (1) builds validated *clean seeds* from a corpus, (2) applies typed **Failure Operators** with controllable severity under a *matched context budget*, and (3) evaluates models so performance drops can be attributed to failure type. On a frozen 500-page Wikipedia pilot (7,489 chunks), three independent dataset builds (seeds 42/123/2026) yield stable automatic funnels (QA acceptance **28.9% ± 0.5%**, failure verification **97.0% ± 0.1%**) and stable human quality (clean **HAR 86.0% ± 2.6%**, stratified failure validity **99.8% ± 0.2%**). On the primary eval run (`pilot_stability_s42`), both **nova-pro** and **llama** show large drops under `missing_evidence` and `hard_negative` (accuracy ≈ 0.02–0.04, abstention ≈ 0.87–0.91), a moderate drop under `conflict` (≈ −11–12 points), and near-ceiling robustness to `context_noise`, `chunk_boundary`, and `evidence_position`. We release code, configs, and regenerable artifacts so others can ablate operators rather than only download a frozen question set.

**Keywords:** RAG evaluation, failure diagnosis, controllable benchmarks, reproducibility

---

## 1. Introduction

RAG pipelines couple retrieval, chunking, and generation. Failures often arise *before* the generator: evidence is missing, buried in noise, split across chunks, placed poorly in a long context, contradicted by other passages, or replaced by near-miss distractors. Existing suites (RGB, CRUD, RAGBench, and related) primarily score **end-task performance** on fixed or semi-fixed items. They rarely expose a **controllable failure taxonomy** with severity knobs and matched clean vs. failed contexts.

**Contributions.**

1. **Failure Operators** — a typed, parameterizable API that transforms clean seeds into failure cases (`missing_evidence`, `context_noise`, `chunk_boundary`, `evidence_position`, `conflict`, `hard_negative`).
2. **Matched-budget diagnosis** — clean and failed conditions share a context chunk budget so drops are not confounded by length.
3. **Regenerable toolchain** — Wikipedia → chunks → QA → validate → inject → evaluate, with multi-seed stability reporting and human-review (HAR) hooks.
4. **Pilot evidence** — stability across three seeds on a frozen M1 corpus; dual-model evaluation showing operator-specific degradation patterns.

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
| Corpus | 500 English Wikipedia pages → **7,489** chunks (frozen) |
| Categories | person, location, science_technology, historical_event, organization_product |
| Candidates / seeds | 500 candidates → 100 clean seeds per run |
| Context budget | 8 chunks (clean and failed) |
| Generation model | Qwen2.5-7B-Instruct (`CHAT_*`) |
| Eval models | `nova-pro`, `llama` on shared `EVAL_*` gateway |
| Primary eval run | `pilot_stability_s42` (100 clean + ~1.7k failures × 2 models) |

**Provenance note.** Pilot fetch uses live MediaWiki API (not a dated dump). Formal release should pin revisions.

---

## 5. Results

### 5.1 Pipeline stability (frozen M1, three seeds)

| Metric | mean ± std |
|--------|------------|
| Candidate QA count | 500.0 ± 0.0 |
| Schema success | 99.7% ± 0.1% |
| QA acceptance | **28.9% ± 0.5%** |
| Clean-seed count | 100.0 ± 0.0 |
| Failure verification pass | **97.0% ± 0.1%** |
| Human acceptance (HAR) | **86.0% ± 2.6%** |
| Human failure validity | **99.8% ± 0.2%** |

| run_id | accept% | fail_pass% | HAR | fail validity |
|--------|---------|------------|-----|---------------|
| `pilot_stability_s42` | 28.6% | 97.1% | 83.0% | 100% (204/204) |
| `pilot_stability_s123` | 29.4% | 96.9% | 87.0% | 99.7% (305/306) |
| `pilot_stability_s2026` | 28.6% | 97.1% | 88.0% | 99.7% (305/306) |

Acceptance is intentionally low: strict filters (notably `title_leak_in_question` and `min_quality_score ≥ 0.85`). Yield at 20% is by construction (`100/500`). After difficulty-quota regeneration, clean-seed difficulty mixes are aligned (~44–47 easy / 38–40 medium / 14–18 hard).

### 5.2 Human audit

| Run | Clean HAR | Failure sample validity |
|-----|-----------|-------------------------|
| `pilot_stability_s42` | 83% (83/100 keep) | 100% (204/204; 4 operators × 51) |
| `pilot_stability_s123` | 87% (87/100 keep) | 99.7% (305/306; 6 operators × 51) |
| `pilot_stability_s2026` | 88% (88/100 keep) | 99.7% (305/306; 6 operators × 51) |
| **mean ± std** | **86.0% ± 2.6%** | **99.8% ± 0.2%** |

Interpret HAR as quality of *selected* seeds, not of raw candidates. Low automatic acceptance (~29%) and high HAR (~86%) are compatible: the filter is strict; humans audit the retained set. Failure samples for s42 predate full `conflict` / `hard_negative` export coverage; s123/s2026 cover all six operators.

### 5.3 Model × operator (RQ1, RQ3) — `pilot_stability_s42`

Clean accuracy: nova-pro **0.93**, llama **0.92**. Robustness scores: **0.66** / **0.69**.

| Condition | nova-pro acc (Δ) | llama acc (Δ) | nova abst | llama abst |
|-----------|------------------|---------------|-----------|------------|
| clean | 0.93 | 0.92 | — | — |
| missing_evidence | 0.03 (−0.90) | 0.02 (−0.90) | 0.87 | 0.91 |
| hard_negative | 0.04 (−0.89) | 0.04 (−0.88) | 0.88 | 0.89 |
| conflict | 0.82 (−0.11) | 0.80 (−0.12) | 0.04 | 0.03 |
| context_noise | 0.86 (−0.07) | 0.93 (+0.01) | 0.06 | 0.01 |
| chunk_boundary | 0.89 (−0.04) | 0.91 (−0.01) | 0.07 | 0.03 |
| evidence_position | 0.91 (−0.02) | 0.93 (+0.01) | 0.04 | 0.01 |

**Findings.**

- **Absence operators work:** both models mostly abstain when gold is removed (`missing_evidence`, `hard_negative`).
- **Conflict hurts moderately:** ~11–12 point drop while gold remains present.
- **Noise / boundary / position are weak stressors** for these strong models under the current severities—useful negative result for diagnosis (aggregate accuracy alone would hide this heterogeneity).
- **Cross-model pattern is consistent** (RQ3): same operator ranking for both systems.

### 5.4 RQ2 (severity / difficulty)

Severity curves and difficulty-conditioned drops: report from `failure_metrics.json` / per-severity splits in the eval report (fill detailed plots in camera-ready). Difficulty quotas stabilize seed composition across runs; operator severity remains the primary controllable axis for degradation curves.

---

## 6. Limitations

- Live MediaWiki pilot ≠ pinned dump.
- `hard_negative` uses lexical overlap, not dense retrieval scores.
- `conflict` alternates are template/rewrite-based; may be stylistically unnatural.
- Weak drops on noise/position may indicate operator under-stress or model strength; harder settings or weaker models needed before claiming those operators “solved.”
- s42 human failure sample covers 4 operators; full 6-operator stratified audit is on s123/s2026.
- Single annotator for pilot HAR; inter-annotator agreement not yet measured.
- Single-hop Wikipedia facts; multi-hop / enterprise docs are future work.

---

## 7. Conclusion

RAGFailBench reframes RAG evaluation as **controllable failure injection + matched-budget diagnosis**. The pilot shows reproducible dataset construction on a frozen corpus (automatic funnels and human HAR stable across three seeds) and clear operator-specific behavior: absence and hard negatives dominate drops; conflict is intermediate; several classic context stressors barely move strong-model accuracy. The artifact is a regenerable generator, not a static leaderboard dump.

---

## Reproducibility

```bash
make setup && make test
make stability-freeze && make stability-run && make stability-report
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml -m nova-pro
python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml -m llama
python -m ragfailbench report -c configs/stability/pilot_stability_s42.yaml
```

Code: https://github.com/taixingbi/RAGFailBench  
Key artifacts: `reports/pilot_stability/`, `reports/pilot_stability_s42/failure_metrics.json`, `reviews/pilot_stability_s*/`, `configs/stability/`.

---

## Checklist (draft → submission)

- [x] Operator taxonomy (6) + matched budget
- [x] Stability table (3 seeds, difficulty quotas aligned)
- [x] Dual-model operator table (s42)
- [x] Fill s123 + s2026 HAR; refresh stability HAR mean±std (**86.0% ± 2.6%**)
- [ ] Severity curves (RQ2 figures)
- [ ] Related-work depth + baselines discussion
- [ ] Pin dump / revision for camera-ready data claim
- [ ] Inter-annotator agreement (κ) on a subset
