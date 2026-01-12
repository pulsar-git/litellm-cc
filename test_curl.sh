#!/bin/bash

# Test LiteLLM proxy with ClaudeCode model

#curl -X GET http://localhost:4000/v1/models \
#  -H "accept: application/json" \
#  -H "content-type: application/json" \
#  -H "authorization: Bearer sk-1234"  | jq .

curl -X POST http://localhost:4000/v1/chat/completions \
  -H "accept: application/json" \
  -H "content-type: application/json" \
  -H "authorization: Bearer sk-1234" \
  -d '{
  "model": "claude-opus-4-5-20251101",
  "messages": [
    {
      "role": "user",
      "content": "Hello! What is your name?"
    }
  ],
  "max_tokens": 100
}' | jq .
