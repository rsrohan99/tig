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
from tig.tools import (
    list_files,
    ask_followup_questions,
    list_code_definitions,
    read_file,
)


class NewTaskCreated(Event):
    pass


class PromptGenerated(Event):
    prompt: str
    is_system_prompt: bool = False


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
        task = ev.get("task")
        await ctx.set("task", task)
        return NewTaskCreated()

    @step
    async def generate_system_prompt(
        self, ctx: Context, ev: NewTaskCreated
    ) -> PromptGenerated:
        task = await ctx.get("task")
        system_prompt = get_system_prompt(self.mode, task)
        return PromptGenerated(prompt=system_prompt, is_system_prompt=True)

    @step
    async def prompt_llm(self, ev: PromptGenerated) -> LLMResponded:
        prompt = ev.prompt
        print(prompt)
        if ev.is_system_prompt:
            self.chat_history.append(ChatMessage(role="system", content=prompt))
        else:
            self.chat_history.append(ChatMessage(role="user", content=prompt))
        response = await self.llm.achat(messages=self.chat_history)
        self.chat_history.append(ChatMessage(role="assistant", content=str(response)))
        return LLMResponded(response=str(response))

    @step
    async def handle_response(
        self, ev: LLMResponded
    ) -> ToolCallRequired | PromptGenerated:
        response = ev.response
        pattern = r"<(?P<tag>(?!thinking\b)\w+)[^>]*>.*</(?P=tag)>"
        match = re.search(pattern, response, re.DOTALL)
        if not match:
            return PromptGenerated(
                prompt="You did not use any tool, please use appropriate tool using valid xml format."
            )
        clean_response = re.sub(
            r"<(?P<tag>\w+)[^>]*>.*?</(?P=tag)>", "", response, flags=re.DOTALL
        ).strip()
        clean_response = re.sub(
            r"```xml.*?```", "", clean_response, flags=re.DOTALL
        ).strip()
        print(f"\n{clean_response}\n")
        # print(f"\n{response}\n")
        tool = parse(match.group())
        return ToolCallRequired(tool=tool)

    @step
    async def use_tool(self, ev: ToolCallRequired) -> PromptGenerated | StopEvent:
        tool_name = list(ev.tool.keys())[0]
        tool_arguments = ev.tool[tool_name]
        print(f"\n🛠️ Using tool: {tool_name}\n")
        try:
            if tool_name == "list_files":
                return PromptGenerated(prompt=list_files(tool_arguments))
            elif tool_name == "ask_followup_question":
                return PromptGenerated(
                    prompt=ask_followup_questions(tool_arguments),
                )
            elif tool_name == "read_file":
                return PromptGenerated(
                    prompt=read_file(tool_arguments, self.auto_approve),
                )
            elif tool_name == "list_code_definition_names":
                return PromptGenerated(
                    prompt=list_code_definitions(tool_arguments, self.auto_approve),
                )
            elif tool_name == "attempt_completion":
                if "result" in tool_arguments:
                    print(f"\n{tool_arguments['result']}\n")
                return StopEvent(message="Task completed successfully.")
            else:
                return PromptGenerated(
                    prompt=f"Tool {tool_name} is not a valid tool. Please use a valid tool."
                )
        except Exception as e:
            return PromptGenerated(
                prompt=f'Error occurred while using tool "{tool_name}": {str(e)}\nMake sure to use tools correctly in valid xml format and valid arguments.'
            )
