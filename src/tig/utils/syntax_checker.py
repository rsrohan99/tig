import collections

from tree_sitter import Node
from tig.services.tree_sitter.parsers import get_parser


def get_errors(root_node: Node):
    errors = []
    nodes_to_visit = [root_node]
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        # print(
        #     f"{node.type} at {node.start_point} - {node.end_point}, {node.is_error}, {node.is_missing}, {node.has_error}"
        # )
        if node.is_error or node.is_missing:
            errors.append(
                {
                    "node": node,  # Keep the node object itself if needed later
                    "type": node.type,  # The type of node ('ERROR', 'MISSING identifier', etc.)
                    "start_point": node.start_point,  # Tuple (row, column) 0-indexed
                    "end_point": node.end_point,  # Tuple (row, column) 0-indexed
                }
            )
        nodes_to_visit.extend(reversed(node.children))
        # sort errors by start_point row, if same row, then end_point row
        errors.sort(key=lambda x: (x["start_point"][0], x["end_point"][0]))
    return errors


def check_syntax(code, extension):
    lines = code.splitlines()
    parser, _ = get_parser(extension)
    tree = parser.parse(bytes(code, "utf8"))
    errors = get_errors(tree.root_node)
    if not errors:
        return ""
    # 1. Determine all lines to display (error lines + context)
    # Use 0-based line indices internally
    lines_to_print = set()
    # Map: line_index (0-based) -> error message for that line
    errors_on_line = collections.defaultdict(str)

    for error in errors:
        start_row, start_col = error["start_point"]
        end_row, end_col = error["end_point"]

        # Add context lines (2 before start, 2 after end)
        context_start = max(0, start_row - 2)
        # Add 3 because range end is exclusive and we want line end_row + 2 included
        context_end = min(len(lines), end_row + 3)

        for i in range(context_start, context_end):
            lines_to_print.add(i)

        # Map error to its start line
        errors_on_line[start_row] = (
            f"        <--- Problem here at Line {start_row + 1}:{start_col + 1}, type: {error['type']}"
        )
        # Map error to its end line *if* it's different from the start line
        # Avoids double-mapping for single-line errors if needed,
        if end_row != start_row:
            errors_on_line[end_row] = (
                f"        <--- Problem here at Line {end_row + 1}:{end_col + 1}, type: {error['type']}"
            )

    # 2. Generate the output string
    result_output_lines = []
    last_printed_line = -1  # Use 0-based index tracking
    sorted_lines_to_print = sorted(list(lines_to_print))

    for line_num in sorted_lines_to_print:
        # Ensure we don't try to access lines beyond the actual code length
        if line_num >= len(lines):
            continue

        # Add separator for non-contiguous blocks
        if line_num > last_printed_line + 1:
            result_output_lines.append("-" * 80)

        line_content = lines[line_num]
        display_line_num = line_num + 1  # For user output (1-based)
        line_output = f"{display_line_num:4d} | {line_content}"

        if line_num in errors_on_line:
            line_output += errors_on_line[line_num]

        result_output_lines.append(line_output)

        last_printed_line = line_num

    return "\n".join(result_output_lines)
