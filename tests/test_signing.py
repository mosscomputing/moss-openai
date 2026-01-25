"""Tests for moss-openai signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_openai import (
    sign_completion,
    sign_tool_call,
    sign_function_call,
    sign_message,
    verify_envelope,
    SignResult,
)


class TestSignToolCall:
    """Test sign_tool_call function."""
    
    def test_sign_tool_call_dict(self):
        """Sign a tool call from dict."""
        tool_call = {
            "id": "call_123",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "NYC"}',
            },
        }
        
        result = sign_tool_call(tool_call, agent_id="test-agent")
        
        assert isinstance(result, SignResult)
        assert result.envelope is not None
        assert result.payload["type"] == "tool_call"
        assert result.payload["name"] == "get_weather"
    
    def test_sign_tool_call_object(self):
        """Sign a tool call from mock object."""
        func = MagicMock()
        func.name = "send_email"
        func.arguments = '{"to": "user@example.com"}'
        
        tool_call = MagicMock()
        tool_call.id = "call_456"
        tool_call.function = func
        
        result = sign_tool_call(tool_call, agent_id="email-agent")
        
        assert result.payload["name"] == "send_email"
        assert result.payload["id"] == "call_456"
    
    def test_sign_tool_call_with_context(self):
        """Sign tool call with context."""
        tool_call = {
            "id": "call_789",
            "function": {"name": "transfer", "arguments": "{}"},
        }
        
        result = sign_tool_call(
            tool_call,
            agent_id="finance-agent",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignCompletion:
    """Test sign_completion function."""
    
    def test_sign_completion_dict(self):
        """Sign a completion from dict."""
        completion = {
            "id": "chatcmpl-123",
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        
        result = sign_completion(completion, agent_id="test-agent")
        
        assert result.payload["type"] == "completion"
        assert result.payload["model"] == "gpt-4"
        assert len(result.payload["choices"]) == 1
    
    def test_sign_completion_object(self):
        """Sign a completion from mock object."""
        message = MagicMock()
        message.role = "assistant"
        message.content = "Hi there!"
        message.tool_calls = None
        
        choice = MagicMock()
        choice.index = 0
        choice.message = message
        choice.finish_reason = "stop"
        
        completion = MagicMock()
        completion.id = "chatcmpl-456"
        completion.model = "gpt-4-turbo"
        completion.choices = [choice]
        
        result = sign_completion(completion, agent_id="test-agent")
        
        assert result.payload["model"] == "gpt-4-turbo"


class TestSignMessage:
    """Test sign_message function."""
    
    def test_sign_message_dict(self):
        """Sign a message from dict."""
        message = {
            "role": "assistant",
            "content": "Hello!",
        }
        
        result = sign_message(message, agent_id="test-agent")
        
        assert result.payload["type"] == "message"
        assert result.payload["content"] == "Hello!"


class TestSignFunctionCall:
    """Test sign_function_call function (legacy)."""
    
    def test_sign_function_call_dict(self):
        """Sign a legacy function call."""
        function_call = {
            "name": "get_weather",
            "arguments": '{"location": "NYC"}',
        }
        
        result = sign_function_call(function_call, agent_id="test-agent")
        
        assert result.payload["type"] == "function_call"
        assert result.payload["name"] == "get_weather"


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        tool_call = {"id": "call_1", "function": {"name": "test", "arguments": "{}"}}
        sign_result = sign_tool_call(tool_call, agent_id="test-agent")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
