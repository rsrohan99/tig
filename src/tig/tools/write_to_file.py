import inquirer


def write_to_file(arguments: dict, mode: str, auto_approve: bool = False) -> str:
    """
    Write the content to a file.
    Args:
        arguments (dict): A dictionary containing the file path and content.
            path (str): The path to the file where content will be written.
            content (str): The content to be written to the file.
        auto_approve (bool): A flag indicating whether to auto-approve the action.
        mode (str): The mode in which Tig is running.
    """
    if "path" not in arguments or "content" not in arguments:
        return "Error: Missing 'path' or 'content' in arguments. Both are required for write_to_file tool."
    if mode == 'architect' and not arguments.get("path", "").endswith(".md"):
        return "Error: Error while running write_to_file tool. In architect mode, you are only allowed to write to markdown files, do not try to write to other files in 'architect' mode."
    file_path = arguments["path"]
    content = arguments["content"]
    lines = content.split("\n")
    print(f"\n# Tig is about to write the following content to '{file_path}':")
    print("-" * 80)
    for line_num, line in enumerate(lines):
        print(f"{line_num + 1} | {line}")
    print("-" * 80)
    if not auto_approve:
        # Ask for confirmation if not auto-approving
        questions = [
            inquirer.Confirm(
                "confirm",
                message=f"Allow Tig to write above content to '{file_path}'?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers and not answers["confirm"]:
            return f"Error: User denied permission to write to '{file_path}'."
    with open(file_path, "w") as f:
        f.write(content)
    return f"[write_to_file for '{file_path}'] Result:\nThe content was successfully written to '{file_path}'.\n"
