import inquirer
import asyncio
from typing import List

# from llama_index.core.llms import ChatMessage

# from workflows.render_resume import RenderResumeWorkflow
# from utils.verbose import log_events


async def cli():
    print("here")
    # chat_history: List[ChatMessage] = []
    # while True:
    #     user_msg = input("\n> ")
    #     if user_msg.lower() == "exit":
    #         break
    #     chat_history.append(ChatMessage(role="user", content=user_msg))
    #     handler = RenderResumeWorkflow.run(user_msg=user_msg, chat_history=chat_history)
    #     await log_events(handler, chat_history=chat_history)
    #     await handler


def main():
    asyncio.run(cli())
