# moss-openai

MOSS signing integration for OpenAI SDK. **Unsigned output is broken output.**

[![PyPI](https://img.shields.io/pypi/v/moss-openai)](https://pypi.org/project/moss-openai/)

## Installation

```bash
pip install moss-openai
```

## Quick Start

Sign tool calls, completions, and messages from OpenAI:

```python
from openai import OpenAI
from moss_openai import sign_tool_call, sign_completion, sign_message

client = OpenAI()

# Get a completion with tool calls
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[{"type": "function", "function": {"name": "get_weather", ...}}]
)

# Sign the completion
result = sign_completion(response, agent_id="weather-bot")
print(f"Signed: {result.signature[:20]}...")

# Sign individual tool calls
for choice in response.choices:
    if choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            result = sign_tool_call(tool_call, agent_id="weather-bot")
```

## Enterprise Mode

Set `MOSS_API_KEY` for automatic policy evaluation:

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_openai import sign_tool_call, enterprise_enabled

print(f"Enterprise: {enterprise_enabled()}")  # True

result = sign_tool_call(
    tool_call,
    agent_id="finance-bot",
    context={"user_id": "u123"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## Verification

```python
from moss_openai import verify_envelope

verify_result = verify_envelope(result.envelope)
if verify_result.valid:
    print(f"Signed by: {verify_result.subject}")
```

## All Functions

| Function | Description |
|----------|-------------|
| `sign_tool_call()` | Sign a tool call |
| `sign_tool_call_async()` | Async version |
| `sign_completion()` | Sign a ChatCompletion |
| `sign_completion_async()` | Async version |
| `sign_message()` | Sign a message |
| `sign_message_async()` | Async version |
| `sign_function_call()` | Sign legacy function call |
| `sign_function_call_async()` | Async version |
| `verify_envelope()` | Verify a signed envelope |

## Enterprise Features

| Feature | Free | Enterprise |
|---------|------|------------|
| Local signing | ✓ | ✓ |
| Offline verification | ✓ | ✓ |
| Policy evaluation | - | ✓ |
| Evidence retention | - | ✓ |
| Audit exports | - | ✓ |

## Links

- [moss-sdk](https://pypi.org/project/moss-sdk/) - Core MOSS SDK
- [mosscomputing.com](https://mosscomputing.com) - Project site

## License

This package is licensed under the [Business Source License 1.1](LICENSE).

- Free for evaluation, testing, and development
- Free for non-production use
- Production use requires a [MOSS subscription](https://mosscomputing.com/pricing)
- Converts to Apache 2.0 on January 25, 2030
