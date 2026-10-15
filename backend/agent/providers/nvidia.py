# pyright: reportUnknownVariableType=false
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from agent.providers.base import (
    EventSink,
    ExecutedToolCall,
    ProviderSession,
    ProviderTurn,
    StreamEvent,
)
from agent.providers.openai import (
    _fit_image_off_loop,
    _get_image_detail_for_model,
    _get_max_patches_for_model,
)
from agent.tools import CanonicalToolDefinition, ToolCall, parse_json_arguments
from agent.state import ensure_str
from costs.token_usage import TokenUsage
from fs_logging.agent_runs import AgentRunRecorder
from fs_logging.prompt_reports import PromptReportLogger
from llm import Llm


def _convert_message_to_chat_completions(
    message: ChatCompletionMessageParam,
    image_detail: str = "high",
) -> Dict[str, Any]:
    role = message.get("role", "user")
    content = message.get("content", "")

    if isinstance(content, str):
        return {"role": role, "content": content}

    parts: List[Dict[str, Any]] = []
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                parts.append({"type": "text", "text": part.get("text", "")})
            elif part.get("type") == "image_url":
                image_url = part.get("image_url", {})
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url.get("url", ""),
                            "detail": image_detail,
                        },
                    }
                )

    return {"role": role, "content": parts}


def _serialize_chat_completions_tools(
    tools: List[CanonicalToolDefinition],
) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for tool in tools:
        serialized.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
        )
    return serialized


@dataclass
class NvidiaParseState:
    assistant_text: str = ""
    tool_calls: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class NvidiaProviderSession(ProviderSession):
    def __init__(
        self,
        client: AsyncOpenAI,
        model: Llm,
        prompt_messages: List[ChatCompletionMessageParam],
        tools: List[Dict[str, Any]],
        recorder: Optional[AgentRunRecorder] = None,
    ):
        self._client = client
        self._model = model
        self._tools = tools
        self._total_usage = TokenUsage()
        self._recorder = recorder
        self._prompt_report_logger = PromptReportLogger(
            provider="nvidia",
            model=model,
            api_model_name=model.value,
        )
        image_detail = _get_image_detail_for_model(model)
        self._messages: List[Dict[str, Any]] = [
            _convert_message_to_chat_completions(message, image_detail=image_detail)
            for message in prompt_messages
        ]
        self._max_patches = _get_max_patches_for_model(model)
        self._prompt_images_fitted = self._max_patches is None

    async def _fit_prompt_images(self) -> None:
        if self._prompt_images_fitted or self._max_patches is None:
            return
        for message in self._messages:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if part.get("type") == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url:
                        part["image_url"]["url"] = await _fit_image_off_loop(
                            url, self._max_patches
                        )
        self._prompt_images_fitted = True

    async def stream_turn(self, on_event: EventSink) -> ProviderTurn:
        await self._fit_prompt_images()
        params: Dict[str, Any] = {
            "model": self._model.value,
            "messages": self._messages,
            "tools": self._tools,
            "tool_choice": "auto",
            "stream": True,
            "max_tokens": 50000,
        }

        self._prompt_report_logger.record_request(params)
        if self._recorder is not None:
            self._recorder.record_llm_request("nvidia", self._model.value, params)

        state = NvidiaParseState()
        stream = await self._client.chat.completions.create(**params)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                state.assistant_text += delta.content
                await on_event(StreamEvent(type="assistant_delta", text=delta.content))
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    call_id = tc.id or f"call-{uuid.uuid4().hex[:6]}"
                    entry = state.tool_calls.setdefault(
                        call_id,
                        {
                            "id": call_id,
                            "name": tc.function.name if tc.function else None,
                            "arguments": "",
                        },
                    )
                    if tc.function and tc.function.name:
                        entry["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        entry["arguments"] += tc.function.arguments
                    await on_event(
                        StreamEvent(
                            type="tool_call_delta",
                            tool_call_id=call_id,
                            tool_name=entry.get("name"),
                            tool_arguments=entry.get("arguments"),
                        )
                    )

        tool_calls: List[ToolCall] = []
        for entry in state.tool_calls.values():
            args, error = parse_json_arguments(entry.get("arguments"))
            if error:
                args = {"INVALID_JSON": ensure_str(entry.get("arguments"))}
            tool_calls.append(
                ToolCall(
                    id=entry.get("id") or f"call-{uuid.uuid4().hex[:6]}",
                    name=entry.get("name") or "unknown_tool",
                    arguments=args,
                )
            )

        if self._recorder is not None:
            self._recorder.record_llm_response(
                state.assistant_text, tool_calls, None
            )
        return ProviderTurn(
            assistant_text=state.assistant_text,
            tool_calls=tool_calls,
            assistant_turn=None,
        )

    def total_cost_usd(self) -> Optional[float]:
        return None

    async def append_tool_results(
        self,
        turn: ProviderTurn,
        executed_tool_calls: list[ExecutedToolCall],
    ) -> None:
        if turn.assistant_text:
            self._messages.append(
                {"role": "assistant", "content": turn.assistant_text}
            )

        tool_calls_payload: List[Dict[str, Any]] = []
        for call in turn.tool_calls:
            tool_calls_payload.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
            )
        if tool_calls_payload:
            self._messages.append(
                {"role": "assistant", "tool_calls": tool_calls_payload}
            )

        for executed in executed_tool_calls:
            result_json = json.dumps(executed.result.result)
            self._messages.append(
                {
                    "role": "tool",
                    "tool_call_id": executed.tool_call.id,
                    "content": result_json,
                }
            )

    async def close(self) -> None:
        await self._client.close()
