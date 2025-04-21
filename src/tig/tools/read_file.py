import inquirer
import os
from typing import Dict

from tig.tools.list_files import load_gitignore


def read_lines(file_path, start_line=0, end_line=None):
    """
    Reads lines from a file starting at start_line and ending at end_line.

    :param file_path: Path to the file
    :param start_line: Line number to start reading from (0-based index, default is 0)
    :param end_line: Line number to stop reading at (exclusive, default is end of file)
    :return: List of strings containing file contents where each string is a line in the format "line_num | line_content" and the line number of the end line.
    """
    lines = []

    # If end_line is not provided, set it to None, which means the entire file till the end
    if end_line is None:
        end_line = float("inf")

    last_line_num = 0
    with open(file_path, "r") as file:
        for current_line_num, line in enumerate(file):
            # Only append lines starting from start_line
            if current_line_num >= start_line:
                last_line_num = current_line_num
                lines.append(f"{current_line_num + 1} | {line}")

            # Stop if we've reached the end line
            if current_line_num >= end_line:
                break


    return lines, last_line_num+1


def read_file(arguments: Dict, auto_approve=False) -> str:
    """
    Efficiently reads a file content, from start_line to end_line if specified.
    Args:
        arguments (Dict): A dictionary containing:
            - 'path': The path to the file to read.
            - 'start_line' (optional): The starting line number to read from.
            - 'end_line' (optional): The ending line number to read to.
        auto_approve (bool): If True, automatically approve the tool call.
    Returns:
        str: The content of the file or an error message.
    """

    if "path" not in arguments:
        return "Error: 'path' argument is required for read_file tool."

    path = arguments["path"]
    if not os.path.isfile(path):
        return f"Error: The path '{path}' is not a valid file. A valid file path is required for read_file tool."

    ignore_spec = load_gitignore()
    if ignore_spec is not None and ignore_spec.match_file(str(path)):
        return f"Error: Permission denied to read the file '{path}'. read_file tool is not allowed on this file. Try to complete your task without reading this file."

    if not auto_approve:
        # Ask for confirmation if not auto-approving
        questions = [
            inquirer.Confirm(
                "confirm",
                message=f"Allow Tig to read the file '{path}'?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers and not answers["confirm"]:
            return f"Error: User denied permission to read the file '{path}' while using read_file tool. Try to complete your task without reading this file."

    start_line = 1
    end_line = None
    if "start_line" in arguments:
        start_line = int(arguments["start_line"])
    if "end_line" in arguments:
        end_line = int(arguments["end_line"]) -1
        if start_line > end_line:
            return f"Error: start_line ({start_line}) cannot be greater than end_line ({end_line}) for read_file tool."

    file_lines, last_line_num = read_lines(path, start_line-1, end_line)
    file_contents = "".join(file_lines)
    return f"""
[read_file for '{path}']
Result:
<file>
<path>{path}</path>
<content lines={start_line}-{last_line_num}>
{file_contents}</content>
</file>"""
