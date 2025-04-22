from tree_sitter import Language, Parser, Node


def check_errors(root_node: Node):
    errors = []
    nodes_to_visit = [root_node]
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        print(str(node))
        if node.is_error or node.is_missing:
            errors.append(
                {
                    "node": node,  # Keep the node object itself if needed later
                    "type": node.type,  # The type of node ('ERROR', 'MISSING identifier', etc.)
                    "start_point": node.start_point,  # Tuple (row, column) 0-indexed
                    "end_point": node.end_point,  # Tuple (row, column) 0-indexed
                    # "start_byte": node.start_byte,
                    # "end_byte": node.end_byte,
                    # "is_error": node.is_error,
                    # "is_missing": node.is_missing,
                }
            )
        nodes_to_visit.extend(reversed(node.children))
    return errors


def check_syntax(code, extension):
    if extension == "py":
        import tree_sitter_python

        PY_LANGUAGE = Language(tree_sitter_python.language())
        parser = Parser(PY_LANGUAGE)
        tree = parser.parse(bytes(code, "utf8"))
        errors = check_errors(tree.root_node)
        if errors:
            for error in errors:
                start_row, start_col = error["start_point"]
                end_row, end_col = error["end_point"]
                # Add 1 to rows/cols for user-friendly 1-based indexing if desired
                print(
                    f"Type: {error['type']}, "
                    # f"Missing: {error['is_missing']}, "
                    # f"Error: {error['is_error']}, "
                    f"Range: L{start_row + 1}:{start_col + 1} - L{end_row + 1}:{end_col + 1}"
                )
    else:
        print("Unsupported file type for syntax checking.")
