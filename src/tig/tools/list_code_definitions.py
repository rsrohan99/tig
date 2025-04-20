import os
from typing import Dict

from tig.services.tree_sitter.parsers import get_parser
from tig.tools.list_files import list_files_non_recursively_respecting_gitignore


def get_code_definitions_from_file(path: str) -> list[str]:
    file_ext = path.split(".")[-1]
    with open(path, "r") as file:
        code = file.read()
    lines = code.split("\n")
    parser, query = get_parser(file_ext)
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    captures = query.captures(root_node)
    nodes_to_add = []
    for k, v in captures.items():
        if "name" not in k and "definition" in k:
            nodes_to_add += v
    nodes_to_add = sorted(nodes_to_add, key=lambda x: x.start_point[0])
    definitions = {}
    for node in nodes_to_add:
        if "definition" not in node.type:
            continue
        definition_key = f"{node.start_point.row}-{node.end_point.row}"
        if definition_key not in definitions:
            definitions[definition_key] = (
                f"{node.start_point.row + 1}-{node.end_point.row + 1} | {lines[node.start_point.row]}"
            )
    return list(definitions.values())


def get_code_definitions(path: str) -> Dict[str, str]:
    """
    Get code definitions from a file or directory.
    Args:
        path (str): Path to the file or directory to analyze.
    Returns:
        Dict[str, list[str]]: A dictionary containing the code definitions.
            - 'file': The file path.
            - 'definitions': A list of code definitions.
    """
    if os.path.isfile(path):
        return {path: "\n".join(get_code_definitions_from_file(path))}
    file_to_definitions = {}
    files_in_dir = list_files_non_recursively_respecting_gitignore(path)
    for file in files_in_dir:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            code_definitions_from_file = get_code_definitions_from_file(file_path)
            if code_definitions_from_file:
                file_to_definitions[file_path] = "\n".join(code_definitions_from_file)
    return file_to_definitions


def list_code_definitions(arguments: Dict) -> str:
    """
    List all code definitions in the given file or all files in the directory.
    Args:
        arguments (Dict): A dictionary containing the arguments for the command.
            - 'path': Path to the file or directory to analyze.
    Returns:
        str: A string containing the list of code definitions.
    """

    if not arguments.get("path"):
        return "Error: 'path' argument is required for list_code_definitions tool."
    path = arguments["path"]
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist, which is required by list_code_definitions tool."
    code_definitions = get_code_definitions(path)
    return_message = f'[list_code_definitions_names for "{path}"] Result:\n\n'
    for file, definitions in code_definitions.items():
        return_message += f"# {file}\n{definitions}\n\n"
    return return_message
