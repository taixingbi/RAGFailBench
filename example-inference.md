#### self-host
curl -i http://192.168.86.179:30180/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {
        "role": "user",
        "content": "Introduce New York City."
      }
    ],
    "max_tokens": 128,
    "stream": false
  }'

#### bedrock (nova-pro)
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name bedrock-inference-mvp \
  --query "Stacks[0].Outputs[?OutputKey=='InferenceFunctionUrl'].OutputValue" \
  --output text)
INFERENCE_API_KEY=1234

curl -sS -X POST "${FUNCTION_URL}v1/chat/completions" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-d '{
  "model": "nova-pro",
  "messages": [{"role": "user", "content": "Say hello in one short sentence."}],
  "max_tokens": 64,
  "temperature": 0
}' | jq '{model, answer: .choices[0].message.content, usage}'
echo

#### bedrock (llama) — same gateway + API key, different model id
curl -sS -X POST "${FUNCTION_URL}v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${INFERENCE_API_KEY}" \
  -d '{
    "model": "llama",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}],
    "max_tokens": 64,
    "temperature": 0
  }' | jq '{error, detail, model, answer: .choices[0].message.content, usage}'
echo

#### OpenAI GPT-OSS (marketplace) — same gateway + API key, third eval model
curl -sS -X POST "${FUNCTION_URL}v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${INFERENCE_API_KEY}" \
  -d '{
    "model": "gpt-oss",
    "messages": [{"role": "user", "content": "Say hello in one short sentence."}],
    "max_tokens": 64,
    "temperature": 0
  }' | jq '{error, detail, model, answer: .choices[0].message.content, usage}'
echo

# In RAGFailBench (.env) — same URL + key for all three; no EVAL_MODEL:
#   EVAL_BASE_URL=${FUNCTION_URL}   # may include trailing slash
#   EVAL_API_KEY=${INFERENCE_API_KEY}
# Default evaluate runs nova-pro,llama,gpt-oss (config evaluation.models):
#   python -m ragfailbench evaluate -c configs/stability/pilot_stability_s42.yaml
#   # or: make evaluate-all-s42 / make evaluate-gpt-oss-s42
