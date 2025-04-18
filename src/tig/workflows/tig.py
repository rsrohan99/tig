from typing import List, Any

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


class NewTaskCreated(Event):
    pass


class SystemPromptGenerated(Event):
    system_prompt: str


class LLMResponded(Event):
    llm_response: str


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

    @step
    async def start_new_task(self, ctx: Context, ev: StartEvent) -> NewTaskCreated:
        task = ev.data.get("task")
        await ctx.set("task", task)
        return NewTaskCreated()

    @step
    async def generate_system_prompt(
        self, ctx: Context, ev: NewTaskCreated
    ) -> SystemPromptGenerated:
        task = await ctx.get("task")
        mode = MODES[self.mode]

    @step
    async def prompt_llm(self, ctx: Context, ev: NewTaskCreated) -> LLMResponded:
        task = await ctx.get("task")
        mode = MODES[self.mode]
