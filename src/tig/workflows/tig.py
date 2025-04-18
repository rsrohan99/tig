import re
from typing import Dict, List, Any

from xmltodict import parse
from llama_index.core.llms.llm import LLM
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import (
    step,
    Context,
    Workflow,
    Event,
    StartEvent,
    StopEvent,
)
from tig.modes import MODES
from tig.prompts.system import get_system_prompt


class NewTaskCreated(Event):
    pass


class PromptGenerated(Event):
    prompt: str


class LLMResponded(Event):
    response: str


class ToolCallRequired(Event):
    tool: Dict


class TigWorkflow(Workflow):
    def __init__(
        self,
        *args: Any,
        llm: LLM,
        mode: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.llm = llm
        if mode not in MODES:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.chat_history: List[ChatMessage] = []
        self.auto_approve = False

    @step
    async def start_new_task(self, ctx: Context, ev: StartEvent) -> NewTaskCreated:
        task = ev.data.get("task")
        await ctx.set("task", task)
        return NewTaskCreated()

    @step
    async def generate_system_prompt(
        self, ctx: Context, ev: NewTaskCreated
    ) -> PromptGenerated:
        task = await ctx.get("task")
        system_prompt = get_system_prompt(self.mode, task)
        return PromptGenerated(prompt=system_prompt)

    @step
    async def prompt_llm(self, ev: PromptGenerated) -> LLMResponded:
        prompt = ev.prompt
        self.chat_history.append(ChatMessage(role="user", content=prompt))
        response = await self.llm.achat(messages=self.chat_history)
        self.chat_history.append(ChatMessage(role="assistant", content=str(response)))
        return LLMResponded(response=str(response))

    @step
    async def handle_response(
        self, ev: LLMResponded
    ) -> ToolCallRequired | PromptGenerated:
        response = ev.response
        pattern = r"<(?P<tag>\w+)[^>]*>.*</(?P=tag)>"
        match = re.search(pattern, response, re.DOTALL)
        if not match:
            return PromptGenerated(
                prompt="You did not use any tool, please use appropriate tool using valid xml format."
            )
        tool = parse(match.group())
        return ToolCallRequired(tool=tool)

    @step
    async def use_tool(self, ctx: Context, ev: ToolCallRequired) -> PromptGenerated | StopEvent:

