"""
MOSS OpenAI Signing Functions

Explicit signing functions for OpenAI SDK outputs.
"""

from typing import Any, Dict, Optional, Union
import json

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_tool_call_payload(tool_call: Any) -> Dict[str, Any]:
    """Extract payload from OpenAI tool call."""
    if isinstance(tool_call, dict):
        return {
            "type": "tool_call",
            "id": tool_call.get("id"),
            "name": tool_call.get("function", {}).get("name"),
            "arguments": tool_call.get("function", {}).get("arguments"),
        }
    
    # Handle ChatCompletionMessageToolCall object
    func = getattr(tool_call, "function", None)
    return {
        "type": "tool_call",
        "id": getattr(tool_call, "id", None),
        "name": getattr(func, "name", None) if func else None,
        "arguments": getattr(func, "arguments", None) if func else None,
    }


def _extract_function_call_payload(function_call: Any) -> Dict[str, Any]:
    """Extract payload from legacy OpenAI function call."""
    if isinstance(function_call, dict):
        return {
            "type": "function_call",
            "name": function_call.get("name"),
            "arguments": function_call.get("arguments"),
        }
    
    return {
        "type": "function_call",
        "name": getattr(function_call, "name", None),
        "arguments": getattr(function_call, "arguments", None),
    }


def _extract_message_payload(message: Any) -> Dict[str, Any]:
    """Extract payload from OpenAI message."""
    if isinstance(message, dict):
        return {
            "type": "message",
            "role": message.get("role"),
            "content": message.get("content"),
            "tool_calls": [
                _extract_tool_call_payload(tc)
                for tc in message.get("tool_calls", [])
            ] if message.get("tool_calls") else None,
        }
    
    tool_calls = getattr(message, "tool_calls", None)
    return {
        "type": "message",
        "role": getattr(message, "role", None),
        "content": getattr(message, "content", None),
        "tool_calls": [
            _extract_tool_call_payload(tc)
            for tc in tool_calls
        ] if tool_calls else None,
    }


def _extract_completion_payload(completion: Any) -> Dict[str, Any]:
    """Extract payload from OpenAI ChatCompletion."""
    if isinstance(completion, dict):
        choices = completion.get("choices", [])
        return {
            "type": "completion",
            "id": completion.get("id"),
            "model": completion.get("model"),
            "choices": [
                {
                    "index": c.get("index"),
                    "message": _extract_message_payload(c.get("message", {})),
                    "finish_reason": c.get("finish_reason"),
                }
                for c in choices
            ],
        }
    
    choices = getattr(completion, "choices", [])
    return {
        "type": "completion",
        "id": getattr(completion, "id", None),
        "model": getattr(completion, "model", None),
        "choices": [
            {
                "index": getattr(c, "index", None),
                "message": _extract_message_payload(getattr(c, "message", None)),
                "finish_reason": getattr(c, "finish_reason", None),
            }
            for c in choices
        ],
    }


def sign_completion(
    completion: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an OpenAI ChatCompletion response.
    
    Args:
        completion: ChatCompletion object from OpenAI SDK
        agent_id: Identifier for the agent
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = client.chat.completions.create(...)
        result = sign_completion(response, agent_id="my-agent")
    """
    payload = _extract_completion_payload(completion)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="completion",
        context=context,
    )


async def sign_completion_async(
    completion: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_completion."""
    payload = _extract_completion_payload(completion)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="completion",
        context=context,
    )


def sign_tool_call(
    tool_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an OpenAI tool call.
    
    Tool calls represent actions the model wants to take. These are typically
    the most important outputs to sign for audit and compliance.
    
    Args:
        tool_call: ChatCompletionMessageToolCall object
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = client.chat.completions.create(model="gpt-4", tools=[...])
        
        if response.choices[0].message.tool_calls:
            for tc in response.choices[0].message.tool_calls:
                result = sign_tool_call(tc, agent_id="my-agent")
                
                if result.blocked:
                    print(f"Blocked: {result.enterprise.policy.reason}")
    """
    payload = _extract_tool_call_payload(tool_call)
    tool_name = payload.get("name", "unknown")
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"tool_call:{tool_name}",
        context=context,
    )


async def sign_tool_call_async(
    tool_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_tool_call."""
    payload = _extract_tool_call_payload(tool_call)
    tool_name = payload.get("name", "unknown")
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"tool_call:{tool_name}",
        context=context,
    )


def sign_function_call(
    function_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a legacy OpenAI function call.
    
    Note: Function calls are deprecated in favor of tool calls.
    Use sign_tool_call for new code.
    
    Args:
        function_call: FunctionCall object
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_function_call_payload(function_call)
    func_name = payload.get("name", "unknown")
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"function_call:{func_name}",
        context=context,
    )


async def sign_function_call_async(
    function_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_function_call."""
    payload = _extract_function_call_payload(function_call)
    func_name = payload.get("name", "unknown")
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"function_call:{func_name}",
        context=context,
    )


def sign_message(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an OpenAI message.
    
    Args:
        message: ChatCompletionMessage object
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_message_payload(message)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


async def sign_message_async(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_message."""
    payload = _extract_message_payload(message)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


def verify_envelope(envelope: Any, payload: Any = None) -> VerifyResult:
    """
    Verify a signed envelope.
    
    Args:
        envelope: MOSS Envelope or dict
        payload: Original payload for hash verification (optional)
    
    Returns:
        VerifyResult with valid=True/False and details
    """
    return verify(envelope, payload)
