from tig.utils.tools import TOOL_NAMES, TOOL_PARAM_NAMES


def parse_tool_call(assistant_message: str) -> dict[str, dict[str, str]]:
    """
    Parses an assistant message string assumed to contain at most one
    XML-like tool call block.

    Extracts the tool name and its parameters into a dictionary.

    Args:
        assistant_message: The string potentially containing <tool><param>...</param></tool>

    Returns:
        A Dictionary containing:
        - Key: The name of the tool called (str)
        - value: A dictionary of parameters (dict[str, str]), where keys are parameter
          names and values are the extracted string values. Empty if no tool found
          or no parameters present.
    """
    found_tool_name: str | None = None
    tool_body_start_index: int = -1
    tool_body_end_index: int = -1
    params: dict[str, str] = {}

    # 1. Find the first complete tool call block <tool_name>...</tool_name>
    for name in TOOL_NAMES:
        opening_tag = f"<{name}>"
        start_index = assistant_message.find(opening_tag)

        if start_index != -1:
            closing_tag = f"</{name}>"
            # Search for the closing tag *after* the opening tag
            end_index = assistant_message.find(
                closing_tag, start_index + len(opening_tag)
            )

            if end_index != -1:
                # Found a complete pair. Assume this is the one we want.
                # (This simplifies things; assumes no identical nested tools)
                found_tool_name = name
                tool_body_start_index = start_index + len(opening_tag)
                tool_body_end_index = end_index
                break  # Stop searching once the first complete tool call is found

    # 2. If no complete tool call was found, return None and empty dict
    if not found_tool_name:
        return {}

    # 3. Extract the content *inside* the tool tags
    tool_body = assistant_message[tool_body_start_index:tool_body_end_index]

    # 4. Parse parameters within the tool body
    current_pos = 0
    while current_pos < len(tool_body):
        found_param_in_iteration = False
        # Check if any known parameter tag starts at the current position
        for param_name in TOOL_PARAM_NAMES:
            param_opening_tag = f"<{param_name}>"
            if tool_body[current_pos:].startswith(param_opening_tag):
                param_value_start_index = current_pos + len(param_opening_tag)
                param_closing_tag = f"</{param_name}>"

                param_value_end_index = -1
                # --- Special Case: write_to_file content ---
                # Handle potential closing tags within the content itself
                if found_tool_name == "write_to_file" and param_name == "content":
                    # Find the *last* occurrence of the closing tag within the tool body,
                    # starting the search *after* the opening tag.
                    param_value_end_index = tool_body.rfind(
                        param_closing_tag, param_value_start_index
                    )
                else:
                    # Standard Case: Find the *first* closing tag after the opening tag.
                    param_value_end_index = tool_body.find(
                        param_closing_tag, param_value_start_index
                    )

                # If a valid closing tag was found for this parameter
                if param_value_end_index != -1:
                    param_value = tool_body[
                        param_value_start_index:param_value_end_index
                    ].strip()
                    params[param_name] = param_value

                    # Move current_pos past the entire parameter block
                    current_pos = param_value_end_index + len(param_closing_tag)
                    found_param_in_iteration = True
                    break  # Found a param, restart search for the next param from the new position
                else:
                    # Found an opening tag but no closing tag before the end of the tool body.
                    # This might indicate a truncated message or invalid XML.
                    # We'll skip this broken param and continue searching after its opening tag.
                    current_pos = param_value_start_index
                    found_param_in_iteration = True
                    break  # Skip the broken param opening tag

        # If no parameter tag started at current_pos, advance by one character
        if not found_param_in_iteration:
            current_pos += 1

    return {found_tool_name: params}
