"""
MOSS OpenAI Integration - Cryptographic Signing for OpenAI SDK Outputs

Sign tool calls, completions, and function calls from the OpenAI SDK.

Quick Start:
    from openai import OpenAI
    from moss_openai import sign_tool_call, sign_completion
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "What's the weather?"}],
        tools=[...]
    )
    
    # Sign tool calls (the actions that matter)
    if response.choices[0].message.tool_calls:
        for tc in response.choices[0].message.tool_calls:
            result = sign_tool_call(tc, agent_id="weather-agent")
            print(f"Signature: {result.signature}")

Enterprise Mode:
    Set MOSS_API_KEY environment variable to enable:
    - Policy evaluation (allow/block/reauth)
    - Evidence retention
    - Usage tracking
"""

__version__ = "0.1.0"

from .signing import (
    sign_completion,
    sign_completion_async,
    sign_tool_call,
    sign_tool_call_async,
    sign_function_call,
    sign_function_call_async,
    sign_message,
    sign_message_async,
    verify_envelope,
)

from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

__all__ = [
    "sign_completion",
    "sign_completion_async",
    "sign_tool_call",
    "sign_tool_call_async",
    "sign_function_call",
    "sign_function_call_async",
    "sign_message",
    "sign_message_async",
    "verify_envelope",
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
]
