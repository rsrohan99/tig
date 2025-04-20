import os
import asyncio
import argparse
import inquirer
from dotenv import load_dotenv

# from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.llms.gemini import Gemini

from tig.workflows.tig import TigWorkflow


async def cli():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="🐯 Tig - AI coding agent",
        usage="tig --mode <architect|code>",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["architect", "code"],
        help="Mode to run the agent in. 'architect' for brainstorming and planning the system, 'code' for implementing the plan.",
    )
    args = parser.parse_args()
    os.system("cls" if os.name == "nt" else "clear")

    if args.mode is None:
        questions = [
            inquirer.List(
                "mode",
                message="Select a mode",
                choices=[
                    "architect - Brainstorming and planning the system",
                    "code - Implementing the plan",
                ],
            )
        ]
        answers = inquirer.prompt(questions)
        if answers:
            args.mode = answers["mode"].split("-")[0].strip()
        else:
            print("No mode selected. Exiting.")
            return

    os.system("cls" if os.name == "nt" else "clear")
    print("🐯 Tig - AI coding agent")
    print(f"\nRunning in '{args.mode}' mode.")
    print("\nGive Tig a task to do. Type '/exit' to quit.\n")

    while True:
        new_task = input("\nNew task: ")
        if new_task.lower() == "/exit":
            break
        if not new_task:
            print("\n❌ Please provide a task.")
            continue
        workflow = TigWorkflow(
            llm=Gemini(model="models/gemini-2.0-flash"),
            mode=args.mode,
            timeout=3600,
        )
        # draw_all_possible_flows(workflow)
        await workflow.run(task=new_task)


def main():
    asyncio.run(cli())
