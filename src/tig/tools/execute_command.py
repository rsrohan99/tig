import os
import inquirer

from tig.services.command_runner import run_shell_command


def execute_command(arguments: dict, mode: str = "code", auto_approve=False) -> str:
    """
    Asks the user to execute a command in the terminal.
    Args:
        arguments (dict): A dictionary containing the file path and diff.
            command (str): The command to execute
            cwd (str): The directory from where the user should run the command
            timeout(int): The time in seconds to wait for the command to complete
        auto_approve (bool): A flag indicating whether to auto-approve the action.
        mode (str): The mode in which Tig is running.
    """

    if mode == "architect":
        return "Error: execute_command is not available in architect mode."

    command = arguments.get("command", "")
    cwd = arguments.get("cwd", "")

    if not command:
        return "Error: 'command' argument not provided. 'command' is required for execute_command."

    if cwd:
        absolute_cwd = os.path.abspath(cwd)
        if not os.path.exists(absolute_cwd):
            return f"Error: The specified 'cwd': '{cwd}' does not exist. Please provide a valid directory as 'cwd' for execute_command tool."
    else:
        absolute_cwd = os.getcwd()

    if "timeout" in arguments:
        timeout = int(arguments["timeout"])
    else:
        timeout = 3600

    print(
        f"\n# Tig is about to execute the command: '{command}' inside '{absolute_cwd}':"
    )
    print("-" * 80)
    print(f"> {command}")
    print("-" * 80)
    if not auto_approve:
        questions = [
            inquirer.Confirm(
                "confirm",
                message="Allow Tig to run the above command?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers and not answers["confirm"]:
            feedback = input(
                "Instruct Tig on what to do instead as you have rejected the command execution: "
            )
            return f"[execute_command for command: '{command}' inside '{absolute_cwd}'] Result:\nUser denied permission to execute the command.\nUser has given this instruction: \n<instruction>{feedback}</instruction>\nFeel free to use ask_followup_question tool for further clarification."

    return run_shell_command(command, absolute_cwd, timeout_seconds=timeout)
