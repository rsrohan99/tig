import os


def execute_command(arguments: dict, mode: str = "code") -> str:
    """
    Asks the user to execute a command in the terminal.
    Args:
        arguments (dict): A dictionary containing the file path and diff.
            command (str): The command to execute
            cwd (str): The directory from where the user should run the command
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
        command = f"(cd {absolute_cwd} && {command})"

    print("-" * 80)
    print(
        f"Tig asked you to execute the following command in your terminal:\n\n```\n{command}\n```\nCopy everything between ``` and paste it in your terminal.\n\nAfter you run the command, please provide Tig with the output of the command and any other relevant information or feedback you have.\n\nIf you don't want to run the command, tell tig what to do instead so that it can continue with its task."
    )
    print("-" * 80)
    print("Your response: ", end="")
    feedback_lines = []
    while True:
        feedback = input()
        if feedback.strip() == "":
            break
        feedback_lines.append(feedback)

    feedback = "\n".join(feedback_lines)

    return f"""[execute_command for command: '{command}'{f' in cwd: "{cwd}"' if cwd else ""}]\nUser provided the following response, which includes the output of the command and may also include additional feedback.\n<response>\n{feedback}\n</response>"""
