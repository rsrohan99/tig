import subprocess
from shutil import which
import os
import sys
from typing import Dict
import inquirer


def exec_ripgrep(rg_args: list[str]):
    """
    Executes the ripgrep command with given arguments and returns the stdout.

    Args:
        rg_args: A list of strings representing the command and its arguments.

    Returns:
        The subprocess result object containing stdout, stderr, and return code.

    Raises:
        FileNotFoundError: If the 'rg' command is not found.
        subprocess.CalledProcessError: If ripgrep returns a non-zero exit code.
        Exception: For other potential subprocess errors.
    """
    command = ["rg"] + rg_args
    # print(f"Executing: {' '.join(command)}", file=sys.stderr)  # Optional: for debugging

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result


def regex_search_files(
    arguments: Dict,
    auto_approve: bool = False,
) -> str:
    """
    Performs regex searches on files using ripgrep and formats the results.

    Args:
        arguments: A dictionary containing:
            path: The directory to search within.
            regex: The regular expression pattern (Rust syntax) to search for.
            file_pattern: An optional glob pattern to filter files (default: '*').
        auto_approve: If True, automatically approve the tool call.

    Returns:
        A formatted string containing search results with context, or an empty
        string if no matches are found or an error occurs during execution
        that is handled (like rg not found or no matches exit code).
    """

    if which("rg") is None:
        return "Error: 'rg' command not found. 'rg' is required for search_files tool. Please ensure ripgrep is installed and in your PATH."

    if "path" not in arguments:
        return "Error: 'path' argument is required for search_files tool."
    directory_path = arguments["path"]
    if not os.path.isdir(directory_path):
        return f"Error: The path '{directory_path}' is not a valid directory. A valid directory path is required for search_files tool."

    if "regex" not in arguments:
        return "Error: 'regex' argument is required for search_files tool."

    if "file_pattern" not in arguments:
        file_pattern = "*"
    else:
        file_pattern = arguments["file_pattern"]

    if not auto_approve:
        # Ask for confirmation if not auto-approving
        questions = [
            inquirer.Confirm(
                "confirm",
                message=f"Allow Tig to read contents from '{directory_path}' (file_pattern {file_pattern})?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers and not answers["confirm"]:
            return f"Error: User denied permission to read contents from '{directory_path}' while using search_files tool. Try to complete your task without reading these contents."

    rg_args = [
        "--context",
        "2",  # 2 lines before and after
        "--context-separator",
        "-----",  # Custom separator
        "--heading",  # Don't print file names above matches initially
        "--line-number",  # Include line numbers for context (we'll strip later if needed)
        "--color",
        "never",  # Disable color codes in output for easier parsing
        "--field-context-separator",
        " | ",
        "--field-match-separator",
        "-| ",
        "--max-columns",
        "400",
        "--max-columns-preview",
        "-g",
        "!node_modules/**",
        "-g",
        "!__pycache__/**",
        "-g",
        "!.env",
        "-g",
        "!.git/**",
        "-e",
        arguments["regex"],
    ]

    # Add glob pattern if it's not the default '*'
    if file_pattern != "*":
        # rg uses separate --glob flags for include patterns
        # Ensure the pattern doesn't unintentionally start with '-'
        if file_pattern.startswith("-"):
            print(
                f"Warning: file_pattern '{file_pattern}' starts with '-', prepending './' for safety.",
                file=sys.stderr,
            )
            rg_args.extend(["--glob", f"./{file_pattern}"])
        else:
            rg_args.extend(["--glob", file_pattern])

    # Add the regex pattern and the directory path
    rg_args.append(directory_path)

    try:
        result = exec_ripgrep(rg_args)
        if result and result.returncode == 0:
            raw_output = result.stdout
        elif result and result.returncode == 1 and not result.stderr:
            return f"[search_files for '{arguments['regex']}' in directory: \"{directory_path}\" with file_pattern '{file_pattern}']\nNo matches found."
        else:
            return f"Error using search_files tool for '{arguments['regex']}' in directory: \"{directory_path}\" with file_pattern '{file_pattern}': {result.stderr.strip()}"
    except (FileNotFoundError, subprocess.CalledProcessError, Exception) as e:
        return f"Error using search_files tool for '{arguments['regex']}' in {directory_path} with file_pattern '{file_pattern}': {str(e)}"

    if not raw_output.strip():
        return f"[search_files for '{arguments['regex']}' in directory: \"{directory_path}\" with file_pattern '{file_pattern}']\nNo matches found."

    MAX_RESULTS = 7
    output_lines = raw_output.strip().split("\n\n")[:MAX_RESULTS]

    formatted_matches = "\n\n".join(["# " + result for result in output_lines])
    return f"[search_files for '{arguments['regex']}' in directory: \"{directory_path}\" with file_pattern '{file_pattern}']\nResults:\n\n{formatted_matches}\n"
