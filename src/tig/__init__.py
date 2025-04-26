import os
import readline  # noqa: F401
import asyncio
import argparse
import inquirer
from dotenv import load_dotenv

# from llama_index.utils.workflow import draw_all_possible_flows

from tig.workflows.tig import TigWorkflow
from tig.utils.intro import print_intro
from tig.services.llms import get_llm


async def cli():
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
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
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve actions without user confirmation (use with caution).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=argparse.SUPPRESS,
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

    llm, provider, model_name = get_llm()
    print_intro(args.mode, provider, model_name, args.auto_approve)

    while True:
        new_task = input("\nNew task: ").strip()
        if not new_task:
            print("\n❌ Please provide a task.\n")
            continue
        if new_task.lower() == "/exit":
            break
        if new_task.lower().startswith("/mode"):
            command_args = new_task.split()
            if len(command_args) < 2:
                print(
                    "\nPlease provide a mode. Available modes: 'architect', 'code'. E.g. \"/mode code\"\n"
                )
                continue
            new_mode = command_args[1].strip()
            if new_mode not in ["architect", "code"]:
                print(
                    "\nInvalid mode. Available modes: 'architect', 'code'. E.g. \"/mode code\"\n"
                )
                continue
            args.mode = new_mode
            print_intro(args.mode, provider, model_name, args.auto_approve)
            continue
        if new_task.lower().startswith("/"):
            print(
                "\n❌ Invalid command. Type '/exit' to quit or '/mode <mode_name>' to switch modes.\n"
            )
            continue
        workflow = TigWorkflow(
            llm=llm,
            mode=args.mode,
            auto_approve=args.auto_approve,
            timeout=3600,
        )
        # draw_all_possible_flows(workflow)
        await workflow.run(task=new_task)


def main():
    asyncio.run(cli())
