import litellm
import os

#litellm._turn_on_debug()

#os.environ["CLAUDE_CODE_API_KEY"] = "sk-ant-oat01-"


model="claude-opus-4-5-20251101"
model="claude_code/claude-opus-4-5-20251101"
model="claude-3-5-haiku-20241022"

for model in ["claude_code/claude-opus-4-5-20251101","claude-opus-4-5-20251101","claude-3-5-haiku-20241022"]:
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "Hello! what's your name?"}]
    )
    print(response)

