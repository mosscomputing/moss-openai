# moss-openai

Cryptographic signing for OpenAI SDK outputs using ML-DSA-44 post-quantum signatures.

[![PyPI](https://img.shields.io/pypi/v/moss-openai)](https://pypi.org/project/moss-openai/)
[![License](https://img.shields.io/badge/license-BSL--1.1-blue)](LICENSE)

## Overview

moss-openai integrates MOSS cryptographic signing into your OpenAI SDK usage. Every tool call, completion, and message gets a tamper-evident signature using ML-DSA-44 (NIST FIPS 204), the post-quantum cryptographic standard. This creates an immutable audit trail for compliance, debugging, and accountability.

## Installation

```bash
pip install moss-openai
```

## Quick Start

```python
from openai import OpenAI
from moss_openai import sign_tool_call, sign_completion

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[{"type": "function", "function": {"name": "get_weather", ...}}]
)

# Sign the completion
result = sign_completion(response, agent_id="weather-bot")
print(f"Signed: {result.signature[:20]}...")
```

## Features

- **ML-DSA-44 signatures** - Post-quantum cryptographic standard (NIST FIPS 204)
- **Tool call signing** - Sign every OpenAI tool/function call
- **Completion signing** - Sign ChatCompletion responses
- **Message signing** - Sign individual messages
- **Policy enforcement** - Block high-risk actions with enterprise policies
- **Offline verification** - Verify signatures without network access

## Usage Examples

### Basic Usage

```python
from moss_openai import sign_tool_call, sign_completion, verify_envelope

# Sign individual tool calls
for choice in response.choices:
    if choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            result = sign_tool_call(tool_call, agent_id="my-bot")

# Verify any envelope
verify_result = verify_envelope(result.envelope)
print(f"Valid: {verify_result.valid}, Subject: {verify_result.subject}")
```

### With Policy Enforcement

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_openai import sign_tool_call

result = sign_tool_call(
    tool_call,
    agent_id="finance-bot",
    context={"user_id": "u123"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## API Reference

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
| `enterprise_enabled()` | Check if enterprise mode is active |

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `MOSS_API_KEY` | API key for enterprise features (policy enforcement, SIEM) |
| `MOSS_API_URL` | Custom API endpoint (default: api.mosscomputing.com) |

## Links

- [Documentation](https://docs.mosscomputing.com/sdks/openai)
- [Dashboard](https://app.mosscomputing.com)
- [PyPI](https://pypi.org/project/moss-openai/)

## License

Business Source License 1.1 - Production use requires a [MOSS subscription](https://mosscomputing.com/pricing).
