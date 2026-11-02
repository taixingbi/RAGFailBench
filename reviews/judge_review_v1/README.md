# Judge review v1 (frozen)

Human labels for 270 blind model answers from `pilot_stability_s42` (15 per model x
condition), labeled before the audit_v1 sample was drawn. Kept separate from the
clean-seed / failure audit. `judge_agreement.md` is the result on the 255 answers whose
seeds survive the multi-part filter: agreement 91.0%, Cohen's kappa 0.72.

Open item: two-value conflict answers should be labeled `both`; some are labeled
`yes`. Re-check the conflict rows and recompute with
`ragfailbench judge-agreement -c configs/stability/pilot_stability_s42.yaml`.
