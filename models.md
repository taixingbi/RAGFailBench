# Models

Models used by RAGFailBench, and the full catalog of the Bedrock gateway
([taixingbi/bedrock-lambda](https://github.com/taixingbi/bedrock-lambda), `models/models.json` at `e49297f`).
Endpoints and keys come from `.env` (`CHAT_*` for generation, `EVAL_*` for evaluation); see `.env.example`.

## Roles in the pipeline

| Role | Stage | Request `model` | Underlying model | Endpoint | Config key |
| --- | --- | --- | --- | --- | --- |
| QA generator + validation judge | M2–M3 | `qwen3-32b` | `qwen.qwen3-32b-v1:0` (Qwen3 32B) | Bedrock gateway (`CHAT_BASE_URL`) | `llm.default_model` / `CHAT_MODEL` |
| Evaluated model | M4 | `nova-pro` | `amazon.nova-pro-v1:0` | Bedrock gateway (`EVAL_BASE_URL`) | `evaluation.models` |
| Evaluated model | M4 | `llama` | `us.meta.llama3-3-70b-instruct-v1:0` (Llama 3.3 70B) | Bedrock gateway | `evaluation.models` |
| Evaluated model | M4 | `gpt-oss` | `openai.gpt-oss-120b-1:0` | Bedrock gateway | `evaluation.models` |
| Correctness judge | M4 | `deepseek` | `deepseek.v3.2` (DeepSeek-V3.2) | Bedrock gateway | `evaluation.judge_model` |

Rules:

- The correctness judge must not be one of the evaluated models. `evaluate` refuses to run otherwise
  (`check_judge_independent` in `src/ragfailbench/evaluation/runner.py`).
- The judge should also come from a different model family than the QA generator (Qwen), so no model grades questions it wrote.
- `evaluation.max_tokens` is 1024 because `gpt-oss` spends ~250 tokens on hidden reasoning. At 256 it returned
  empty content while still reporting `finish_reason=stop`.

Bedrock request quotas (us-east-1; these cannot be raised from the account): nova-pro is 25/min on-demand and 50/min through the
`us.` cross-region profile, llama is 80/min, and gpt-oss, deepseek and qwen3-32b are 1000/min. The Lambda account limit is
10 concurrent executions. That is why evaluation routes `nova-pro` to `us.amazon.nova-pro-v1:0`
(`evaluation.model_routes`; results stay labeled `nova-pro`) and runs the three models in parallel with
`evaluation_concurrency: 9`.

Before a long run, check every selected model with one real call each:
`make smoke-models` (or `python scripts/smoke_test_model.py -c <config> [--skip-generator]`).

The generator was the self-hosted `Qwen/Qwen2.5-7B-Instruct` until 2026-10-25. It was replaced by `qwen3-32b`, which
stays in the same family, after a 9-chunk trial of the real QA prompt (3 per difficulty). The trial results:

| Candidate | Parsed | Grounded (supporting sentence verbatim in chunk) | Time | Note |
| --- | --- | --- | --- | --- |
| `qwen3-32b` | 9/9 | 9/9 | 7.6s | **Selected** |
| `ministral-14b` | 9/9 | 7/9 | 10.4s | |
| `gemma-3-27b` | 9/9 | 8/9 | 20.3s | |
| `qwen3-next-80b-a3b` | 9/9 | 8/9 | 26.7s | Its hard question had two parts but a one-part gold answer |

Runs before 2026-10-25 (`pilot_v1`, `pilot_stability_s*`) used `nova-pro` as the judge, because the judge call
fell back to the client's default model. Those results are affected by self-judging.

## Judge candidates

| Request `model` | Verdict | Reason |
| --- | --- | --- |
| `deepseek` | **Selected** | Enabled, strong, independent of all evaluated models and of the generator |
| `gemma-3-27b`, `ministral-14b` | Second-judge option | Independent families; use for judge-agreement reporting |
| `qwen3-next-80b-a3b`, `qwen3-32b` | Rejected | Same family as the QA generator (Qwen) |
| `deepseek-r1` | Rejected | Emits reasoning text that overflows the judge's 60-token JSON budget |
| `nova-*`, `llama*`, `gpt-oss*` | Rejected | Same family as an evaluated model |

## Gateway catalog

"Enabled" means the model is on by default in the gateway's smoke test. Every alias can be requested,
as long as Bedrock model access is granted for the account.

| Request `model` | Bedrock ID | Family | Enabled |
| --- | --- | --- | --- |
| `nova-micro` | `amazon.nova-micro-v1:0` | Amazon Nova | ✅ |
| `nova-lite` | `amazon.nova-lite-v1:0` | Amazon Nova | |
| `nova-pro` | `amazon.nova-pro-v1:0` | Amazon Nova | ✅ |
| `us.amazon.nova-pro-v1:0` | US cross-region profile | Amazon Nova | |
| `llama` / `llama3.3` | `us.meta.llama3-3-70b-instruct-v1:0` | Meta Llama | ✅ |
| `llama4` / `llama4-maverick` | `us.meta.llama4-maverick-17b-instruct-v1:0` | Meta Llama | |
| `llama4-scout` | `us.meta.llama4-scout-17b-instruct-v1:0` | Meta Llama | |
| `gpt-oss` / `gpt-oss-120b` | `openai.gpt-oss-120b-1:0` | OpenAI GPT-OSS | ✅ |
| `gpt-oss-20b` | `openai.gpt-oss-20b-1:0` | OpenAI GPT-OSS | |
| `gpt-oss-safeguard-20b` | `openai.gpt-oss-safeguard-20b` | OpenAI GPT-OSS | ✅ |
| `gpt-oss-safeguard` / `-120b` | `openai.gpt-oss-safeguard-120b` | OpenAI GPT-OSS | ✅ |
| `deepseek` | `deepseek.v3.2` | DeepSeek | ✅ |
| `deepseek-r1` | `us.deepseek.r1-v1:0` | DeepSeek | |
| `qwen3-next-80b-a3b` | `qwen.qwen3-next-80b-a3b` | Qwen | ✅ |
| `qwen3-32b` | `qwen.qwen3-32b-v1:0` | Qwen | |
| `ministral-3b` | `mistral.ministral-3-3b-instruct` | Mistral | |
| `ministral-8b` | `mistral.ministral-3-8b-instruct` | Mistral | |
| `ministral-14b` | `mistral.ministral-3-14b-instruct` | Mistral | |
| `gemma-3-4b` | `google.gemma-3-4b-it` | Google Gemma | |
| `gemma-3-12b` | `google.gemma-3-12b-it` | Google Gemma | |
| `gemma-3-27b` | `google.gemma-3-27b-it` | Google Gemma | |
| `minilm-l12-h384` | in-process classifier (not a chat model) | MiniLM | ✅ |

The gateway also accepts raw Bedrock IDs (e.g. `anthropic.*`), but it has no Claude alias.
