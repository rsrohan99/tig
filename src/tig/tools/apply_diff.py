import re
from textwrap import dedent
from functools import partial

import inquirer
from diff_match_patch import diff_match_patch

# ANSI escape codes
ANSI_STRIKETHROUGH = "\033[9m"
ANSI_UNDERLINE = "\033[4m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_RESET = "\033[0m"


def flush_line(num, content):
    # Print line number padded to 4 spaces + content
    print(f"{num:4d} | {content}")


def pretty_print_diffs_with_line_numbers(diffs):
    dmp = diff_match_patch()
    line_num = 1
    line_buffer = ""
    for op, data in diffs:
        # Split data by lines, keep line breaks to handle line numbers correctly
        lines = data.splitlines(keepends=True)
        for line in lines:
            # Format line content based on diff operation
            if op == dmp.DIFF_INSERT:
                # Underline added text in green
                formatted = (
                    f"{ANSI_GREEN}{ANSI_UNDERLINE}{line.rstrip('\n')}{ANSI_RESET}"
                )
            elif op == dmp.DIFF_DELETE:
                # Strikethrough deleted text in red
                formatted = (
                    f"{ANSI_RED}{ANSI_STRIKETHROUGH}{line.rstrip('\n')}{ANSI_RESET}"
                )
            else:
                # Equal text normal
                formatted = line
            # Append formatted line content to buffer
            line_buffer += formatted
            # If line ends, print line with line number and reset buffer
            if line.endswith("\n"):
                flush_line(line_num, line_buffer.rstrip("\n"))
                line_buffer = ""
                line_num += 1
    # Flush any remaining content not ended by newline
    if line_buffer:
        flush_line(line_num, line_buffer)


def find_string_index(strings: list[str], x):
    total = 0
    for i, s in enumerate(strings):
        if total + len(s) > x:
            return i
        total += len(s)
    raise IndexError("Index x is out of range.")


def get_leading_whitespace(line):
    match = re.match(r"^[\t ]*", line)
    return match.group(0) if match else ""


def adjust_indentation(original_indents, line):
    matched_indent = original_indents[0] if original_indents else ""
    current_indent_match = re.match(r"^[\t ]*", line)
    current_indent = current_indent_match.group(0) if current_indent_match else ""
    # search_base_indent = search_indents[0] if search_indents else ""
    # search_base_level = len(search_base_indent)
    matched_indent_level = len(matched_indent)
    current_level = len(current_indent)
    relative_level = current_level - matched_indent_level
    if relative_level < 0:
        final_indent = matched_indent[: max(0, len(matched_indent) + relative_level)]
    else:
        final_indent = matched_indent + current_indent[matched_indent_level:]
    # print(
    #     f"[{matched_indent}], [{current_indent}], {relative_level}, [{final_indent}] --- {line.strip()}"
    # )
    return final_indent + line.strip()


def strip_line_numbers(content: str, aggressive: bool = False) -> str:
    # Detect the line endings
    line_ending = "\r\n" if "\r\n" in content else "\n"

    # Split into lines
    lines = content.splitlines()

    # Process each line
    processed_lines = []
    for line in lines:
        if aggressive:
            match = re.match(r"^\s*(?:\d+\s)?\|\s(.*)$", line)
        else:
            match = re.match(r"^\s*\d+\s+\|(?!\|)\s?(.*)$", line)
        processed_lines.append(match.group(1) if match else line)

    return line_ending.join(processed_lines)


def every_line_has_line_numbers(content: str) -> bool:
    lines = content.splitlines()
    return len(lines) > 0 and all(
        re.match(r"^\s*\d+\s+\|(?!\|)", line) for line in lines
    )


def unescape_markers(content: str) -> str:
    replacements = {
        r"^\\<<<<<<<": "<<<<<<<",
        r"^\\=======": "=======",
        r"^\\>>>>>>>": ">>>>>>>",
        r"^\\-------": "-------",
        r"^\\:end_line:": ":end_line:",
        r"^\\:start_line:": ":start_line:",
    }

    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def apply_diff(arguments: dict, mode: str, auto_approve: bool = False) -> str:
    """
    Write the content to a file.
    Args:
        arguments (dict): A dictionary containing the file path and diff.
            path (str): The path to the file where content will be written.
            diff (str): properly formatted diff content
        auto_approve (bool): A flag indicating whether to auto-approve the action.
        mode (str): The mode in which Tig is running.
    """
    if "path" not in arguments or "diff" not in arguments:
        return "Error: Missing 'path' or 'diff' in arguments. Both are required for write_to_file tool."
    if mode == "architect" and not arguments.get("path", "").endswith(".md"):
        return "Error: Error while running apply_diff tool. In architect mode, you are only allowed to edit markdown files, do not try to edit other files in 'architect' mode."

    file_path = arguments["path"]
    diff = arguments["diff"]

    original_content = ""
    try:
        with open(file_path, "r") as f:
            original_content = f.read()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found while using apply_diff tool. Please check the file path and try again."

    regex_pattern = r"(?:^|\n)(?<!\\)<<<<<<< SEARCH\s*\n((?:\:start_line:\s*(\d+)\s*\n))?((?:\:end_line:\s*(\d+)\s*\n))?((?<!\\)-------\s*\n)?([\s\S]*?)(?:\n)?(?:(?<=\n)(?<!\\)=======\s*\n)([\s\S]*?)(?:\n)?(?:(?<=\n)(?<!\\)>>>>>>> REPLACE)(?=\n|$)"

    matches = re.findall(regex_pattern, diff)

    if not matches:
        return dedent('''
        Error: invalid search/replace diff format for apply_diff tool. Make sure the diff is correctly formatted. As a reminder to you, here is an example of a valid diff format:
        ---
        Example:

        Original file:
        ```
        1 | def calculate_total(items):
        2 |     total = 0
        3 |     for item in items:
        4 |         total += item
        5 |     return total
        ```

        Search/Replace content:
        ```
        <<<<<<< SEARCH
        :start_line:1
        -------
        def calculate_total(items):
            total = 0
            for item in items:
                total += item
            return total
        =======
        def calculate_total(items):
            """Calculate total with 10% markup"""
            return sum(item * 1.1 for item in items)
        >>>>>>> REPLACE

        ```

        Search/Replace content with multi edits:
        ```
        <<<<<<< SEARCH
        :start_line:1
        -------
        def calculate_total(items):
            sum = 0
        =======
        def calculate_sum(items):
            sum = 0
        >>>>>>> REPLACE

        <<<<<<< SEARCH
        :start_line:4
        -------
                total += item
            return total
        =======
                sum += item
            return sum 
        >>>>>>> REPLACE
        ```

        Usage:
        <apply_diff>
        <path>File path here</path>
        <diff>
        Your search/replace content here
        You can use multi search/replace block in one diff block, but make sure to include the line numbers for each block.
        Only use a single line of '=======' between search and replacement content, because multiple '=======' will corrupt the file.
        </diff>
        </apply_diff>
        ---''')

    replacements = list(
        map(
            lambda match: {
                "start_line": int(match[1]) or 0,
                "search_content": match[5],
                "replace_content": match[6],
            },
            matches,
        )
    )
    replacements.sort(key=lambda x: x["start_line"])
    line_ending = "\r\n" if "\r\n" in original_content else "\n"
    result_lines = re.split(r"\r?\n", original_content)
    delta = 0
    diff_error_messages = []
    successfull_diffs = 0
    for replacement in replacements:
        search_content = str(replacement.get("search_content", ""))
        replace_content = str(replacement.get("replace_content", ""))
        start_line = replacement["start_line"] + (
            0 if replacement["start_line"] == 0 else delta
        )
        has_all_line_numbers = (
            every_line_has_line_numbers(search_content)
            and every_line_has_line_numbers(replace_content)
        ) or (
            not every_line_has_line_numbers(search_content)
            and (replace_content.strip() == "")
        )

        if has_all_line_numbers:
            search_content = strip_line_numbers(search_content)
            replace_content = strip_line_numbers(replace_content)

        if search_content == replace_content:
            diff_error_messages.append(
                "Error: Search and replace content are the same for apply_diff tool. No changes will be made for this diff. Use read_file to verify the content you want to change."
            )
            continue

        search_lines = (
            [] if search_content == "" else re.split(r"\r?\n", search_content)
        )
        replace_lines = (
            [] if replace_content == "" else re.split(r"\r?\n", replace_content)
        )

        if len(search_lines) == 0:
            diff_error_messages.append(
                "Error: search content cannot be empty for apply_diff tool.\nDebug Info:\n- Search content cannot be empty\n- For insertions, provide a specific line using :start_line: and include content to search for\n- For example, match a single line to insert before/after it"
            )
            continue

        match_index = -1
        search_chunk = "\n".join(search_lines)
        exact_start_index = start_line - 1
        search_len = len(search_lines)
        exact_end_index = exact_start_index + search_len - 1
        original_chunk = "\n".join(
            result_lines[exact_start_index : exact_end_index + 1]
        )
        dmp = diff_match_patch()
        dmp.Match_Threshold = 0.1
        found_index = dmp.match_main(original_chunk, search_chunk, 0)
        if found_index == -1:
            diff_error_messages.append(
                f"Error: Search content for this diff was not found in the original file for apply_diff tool.\nDebug Info:\n- Search content:\n{search_chunk}\n---\n- Original content:\n{original_chunk}\n---\nMake sure search content is exactly same as in the file. If you are unsure, use read_file tool to verify the content."
            )
            continue

        match_index = (
            find_string_index(re.split(r"\r?\n", original_chunk), found_index)
            + exact_start_index
        )
        matched_lines = result_lines[match_index : match_index + len(search_lines)]
        original_indents = list(map(get_leading_whitespace, matched_lines))
        partial_adjust_indentation = partial(adjust_indentation, original_indents)
        indented_replace_lines = list(map(partial_adjust_indentation, replace_lines))
        before_match = result_lines[:match_index]
        after_match = result_lines[match_index + len(search_lines) :]
        result_lines = before_match + indented_replace_lines + after_match
        delta = delta - len(matched_lines) + len(replace_lines)
        successfull_diffs += 1

    full_final_content = line_ending.join(result_lines)
    print(f"\n# Tig is about to edit the contents of '{file_path}':")
    print("-" * 80)
    dmp = diff_match_patch()
    diffs = dmp.diff_main(original_content, full_final_content)
    dmp.diff_cleanupSemantic(diffs)
    pretty_print_diffs_with_line_numbers(diffs)
    print("-" * 80)
    if not auto_approve:
        # Ask for confirmation if not auto-approving
        questions = [
            inquirer.Confirm(
                "confirm",
                message=f"Allow Tig to edit the contents in '{file_path}'?",
                default=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers and not answers["confirm"]:
            feedback = input(
                "Instruct Tig on what to do instead as you have rejected the changes: "
            )
            return f"[apply_diff for file: '{file_path}'] Result:\nUser denied permission to edit '{file_path}'.\nUser has given this feedback: \n<feedback>{feedback}</feedback>\nFeel free to use ask_followup_question tool for further clarification."
    with open(file_path, "w") as f:
        f.write(full_final_content)
    result_message = ""
    if len(replacements) == successfull_diffs:
        result_message = f"[apply_diff for '{file_path}'] Result:\nAll {successfull_diffs} out of {len(replacements)} diffs were successfully applied to '{file_path}'.\n"
    elif successfull_diffs > 0 and successfull_diffs < len(replacements):
        result_message = f"[apply_diff for '{file_path}'] Result:\n{successfull_diffs} out of {len(replacements)} diffs were successfully applied to '{file_path}'.\nAs some of the diffs were not applied, make sure to use read_file on '{file_path}' to ensure everything is ok as partially applied diffs may lead to unexpected results.\nHere are some information on why the diffs were not applied:\n{'\n---\n'.join(diff_error_messages)}"
    elif successfull_diffs == 0:
        result_message = f"[apply_diff for '{file_path}'] Result:\nNo diffs were successfully applied to '{file_path}'.\nHere are some information on why the diffs were not applied:\n{'\n---\n'.join(diff_error_messages)}"
    return result_message
