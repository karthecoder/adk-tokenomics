# ruff: noqa
import sys
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps.app import EventsCompactionConfig

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import shared_logic
import prompts

from google.genai import types

# Discover skills for dynamic loading in the skills agent
skills_catalog = shared_logic.discover_skills()

import google.adk.models.anthropic_llm as anthropic_llm_module
from anthropic import types as anthropic_types
from google.adk.models.llm_response import LlmResponse

def get_agent_config():
    budget = shared_logic.get_thinking_budget()
    return types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=budget)
    )

def _patched_build_anthropic_thinking_param(config):
    if not config or not config.thinking_config:
        return anthropic_llm_module.NOT_GIVEN
    budget = config.thinking_config.thinking_budget
    if budget == 0:
        return anthropic_types.ThinkingConfigDisabledParam(type="disabled")
    # Anthropic Adaptive Thinking for Claude Sonnet 5 / Opus 4.7+
    return anthropic_types.ThinkingConfigAdaptiveParam(type="adaptive")

anthropic_llm_module._build_anthropic_thinking_param = _patched_build_anthropic_thinking_param

def _patched_message_to_generate_content_response(message):
    parts = [anthropic_llm_module.content_block_to_part(cb) for cb in message.content]
    thinking_cnt = 0
    if hasattr(message.usage, "output_tokens_details") and message.usage.output_tokens_details:
        val = getattr(message.usage.output_tokens_details, "thinking_tokens", 0)
        try:
            thinking_cnt = int(val)
        except (ValueError, TypeError):
            thinking_cnt = 0
        
    return LlmResponse(
        content=types.Content(role="model", parts=parts),
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=message.usage.input_tokens,
            candidates_token_count=message.usage.output_tokens,
            thoughts_token_count=thinking_cnt,
            total_token_count=(message.usage.input_tokens + message.usage.output_tokens),
        )
    )

def _format_anthropic_system(system_instruction):
    if not system_instruction:
        return anthropic_llm_module.NOT_GIVEN
    if isinstance(system_instruction, str):
        return [{"type": "text", "text": system_instruction}]
    if hasattr(system_instruction, "parts") and system_instruction.parts:
        text_parts = [p.text for p in system_instruction.parts if getattr(p, "text", None)]
        if text_parts:
            return [{"type": "text", "text": "\n".join(text_parts)}]
    if isinstance(system_instruction, list):
        return system_instruction
    return anthropic_llm_module.NOT_GIVEN

async def _patched_generate_content_streaming(
    self,
    llm_request,
    messages,
    tools,
    tool_choice,
    thinking=anthropic_llm_module.NOT_GIVEN,
):
    model_to_use = self._resolve_model_name(llm_request.model)
    system_param = _format_anthropic_system(llm_request.config.system_instruction if llm_request.config else None)
    raw_stream = await self._anthropic_client.messages.create(
        model=model_to_use,
        system=system_param,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        max_tokens=self.max_tokens,
        stream=True,
        thinking=thinking,
    )

    text_blocks = {}
    tool_use_blocks = {}
    thinking_blocks = {}
    redacted_thinking_blocks = {}
    input_tokens = 0
    output_tokens = 0
    thinking_tokens = 0

    async for event in raw_stream:
        if event.type == "message_start":
            input_tokens = event.message.usage.input_tokens
            output_tokens = event.message.usage.output_tokens
        elif event.type == "content_block_start":
            block = event.content_block
            if isinstance(block, anthropic_types.ThinkingBlock):
                thinking_blocks[event.index] = anthropic_llm_module._ThinkingAccumulator(
                    thinking=block.thinking,
                    signature=block.signature,
                )
            elif isinstance(block, anthropic_types.RedactedThinkingBlock):
                redacted_thinking_blocks[event.index] = block.data
            elif isinstance(block, anthropic_types.TextBlock):
                text_blocks[event.index] = block.text
            elif isinstance(block, anthropic_types.ToolUseBlock):
                tool_use_blocks[event.index] = anthropic_llm_module._ToolUseAccumulator(
                    id=block.id,
                    name=block.name,
                    args_json="",
                )
        elif event.type == "content_block_delta":
            delta = event.delta
            if isinstance(delta, anthropic_types.ThinkingDelta):
                thinking_blocks.setdefault(
                    event.index,
                    anthropic_llm_module._ThinkingAccumulator(thinking="", signature=""),
                )
                thinking_blocks[event.index].thinking += delta.thinking
                yield LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=delta.thinking, thought=True)],
                    ),
                    partial=True,
                )
            elif isinstance(delta, anthropic_types.TextDelta):
                text_blocks.setdefault(event.index, "")
                text_blocks[event.index] += delta.text
                yield LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=delta.text)],
                    ),
                    partial=True,
                )
            elif isinstance(delta, anthropic_types.InputJSONDelta):
                if event.index in tool_use_blocks:
                    tool_use_blocks[event.index].args_json += delta.partial_json

        elif event.type == "message_delta":
            output_tokens = event.usage.output_tokens
            if hasattr(event.usage, "output_tokens_details") and event.usage.output_tokens_details:
                thinking_tokens = getattr(event.usage.output_tokens_details, "thinking_tokens", 0) or 0

    all_parts = []
    all_indices = sorted(
        set(
            list(thinking_blocks.keys())
            + list(redacted_thinking_blocks.keys())
            + list(text_blocks.keys())
            + list(tool_use_blocks.keys())
        )
    )
    for idx in all_indices:
        if idx in thinking_blocks:
            acc = thinking_blocks[idx]
            part = types.Part(text=acc.thinking, thought=True)
            if acc.signature:
                part.thought_signature = acc.signature.encode("utf-8")
            all_parts.append(part)
        if idx in redacted_thinking_blocks:
            all_parts.append(
                types.Part(
                    thought=True,
                    thought_signature=redacted_thinking_blocks[idx].encode("utf-8"),
                )
            )
        if idx in text_blocks:
            all_parts.append(types.Part.from_text(text=text_blocks[idx]))
        if idx in tool_use_blocks:
            acc = tool_use_blocks[idx]
            args = json.loads(acc.args_json) if acc.args_json else {}
            part = types.Part.from_function_call(name=acc.name, args=args)
            part.function_call.id = acc.id
            all_parts.append(part)

    yield LlmResponse(
        content=types.Content(role="model", parts=all_parts),
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=input_tokens,
            candidates_token_count=output_tokens,
            thoughts_token_count=thinking_tokens,
            total_token_count=input_tokens + output_tokens,
        ),
        partial=False,
    )

anthropic_llm_module.AnthropicLlm._generate_content_streaming = _patched_generate_content_streaming

# Map UI Thinking Budget to Anthropic Adaptive Effort level (low / medium / high)
_orig_claude_generate_content_async = anthropic_llm_module.Claude.generate_content_async

async def _patched_claude_generate_content_async(self, llm_request, stream=False):
    raw_budget = shared_logic.get_thinking_budget()
    max_tokens = shared_logic.get_max_output_tokens()
    
    if isinstance(raw_budget, str):
        b_str = raw_budget.lower()
        if b_str in ("low", "medium", "high"):
            effort = b_str
        elif b_str == "off":
            effort = "off"
        else:
            effort = "high"
    else:
        if raw_budget <= 0:
            effort = "off"
        elif raw_budget <= 1024:
            effort = "low"
        elif raw_budget <= 2048:
            effort = "medium"
        else:
            effort = "high"
    
    self.max_tokens = max_tokens
    client = self._anthropic_client
    orig_create = client.messages.create

    async def create_with_effort(*args, **kwargs):
        if effort != "off" and kwargs.get("thinking") and getattr(kwargs["thinking"], "type", None) == "adaptive":
            kwargs["output_config"] = {"effort": effort}
        if "system" in kwargs:
            kwargs["system"] = _format_anthropic_system(kwargs["system"])
        return await orig_create(*args, **kwargs)

    client.messages.create = create_with_effort
    try:
        async for resp in _orig_claude_generate_content_async(self, llm_request, stream=stream):
            yield resp
    finally:
        client.messages.create = orig_create

anthropic_llm_module.Claude.generate_content_async = _patched_claude_generate_content_async

from google.adk.models.anthropic_llm import Claude
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.registry import LLMRegistry

# Register custom model name patterns in ADK's global LLMRegistry
LLMRegistry._register(r"claude-.*", Claude)
LLMRegistry._register(r".*sonnet.*", Claude)

_orig_resolve_model_name = anthropic_llm_module.AnthropicLlm._resolve_model_name

def _patched_resolve_model_name(self, model):
    if model and ("claude" in model.lower() or "sonnet" in model.lower()):
        return "claude-sonnet-5"
    return _orig_resolve_model_name(self, model)

anthropic_llm_module.AnthropicLlm._resolve_model_name = _patched_resolve_model_name

def get_model():
    model_name = shared_logic.get_model_name()
    if "claude" in model_name.lower() or "sonnet" in model_name.lower():
        return Claude(model="claude-sonnet-5")
    return Gemini(model=model_name)

class DynamicModel(BaseLlm):
    model: str = "publishers/google/models/gemini-3.5-flash"

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False):
        active_llm = get_model()
        llm_request.model = active_llm.model
        
        # Dynamically hot-reload thinking budget and max output tokens on every turn from UI/env
        raw_budget = shared_logic.get_thinking_budget()
        max_tokens = shared_logic.get_max_output_tokens()
        
        if isinstance(raw_budget, str):
            b_map = {"off": 0, "low": 1024, "medium": 2048, "high": 4096, "dynamic": -1}
            budget = b_map.get(raw_budget.lower(), 4096)
        else:
            budget = int(raw_budget)

        if not llm_request.config:
            llm_request.config = types.GenerateContentConfig()
            
        llm_request.config.thinking_config = types.ThinkingConfig(thinking_budget=budget)
        llm_request.config.max_output_tokens = max_tokens

        async for resp in active_llm.generate_content_async(llm_request, stream=stream):
            yield resp

# 1. Naive App (Scenario 1)
naive_agent = Agent(
    name="naive_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.NAIVE_INSTRUCTION,
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)
naive_app = App(root_agent=naive_agent, name="naive_app")

# 2. Caching App (Scenario 2)
caching_agent = Agent(
    name="caching_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.CACHING_INSTRUCTION,
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)
caching_app = App(
    root_agent=caching_agent,
    name="caching_app",
    context_cache_config=ContextCacheConfig(min_tokens=1024, ttl_seconds=300)
)

# 3. Compaction App (Scenario 3)
compaction_agent = Agent(
    name="compaction_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.COMPACTION_INSTRUCTION,
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)
compaction_app = App(
    root_agent=compaction_agent,
    name="compaction_app",
    events_compaction_config=EventsCompactionConfig(compaction_interval=4, overlap_size=1)
)

# 4. Modular Skills App (Scenario 4)
skills_agent = Agent(
    name="skills_agent",
    model=DynamicModel(),
    generate_content_config=get_agent_config(),
    instruction=prompts.SKILLS_INSTRUCTION_TEMPLATE.format(skills_catalog=skills_catalog),
    tools=[shared_logic.get_weather, shared_logic.get_current_time, shared_logic.activate_skill, shared_logic.google_search],
    after_model_callback=shared_logic.after_model_cb
)
skills_app = App(root_agent=skills_agent, name="skills_app")

# Default app export
app = naive_app
