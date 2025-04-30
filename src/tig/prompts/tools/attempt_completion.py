from textwrap import dedent

ATTEMPT_COMPLETION_PROMPT = dedent("""
## attempt_completion
Description: Present the task result to the user. Optionally provide a CLI command to demo the result.
IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful. Failure to do so will result in code corruption and system failure. Before using this tool, you must ask yourself in <thinking></thinking> tags if you've confirmed from the user that any previous tool uses were successful. If not, then DO NOT use this tool.
Parameters:
- result: (required) The result of the task. Formulate this result in a way that is final and does not require further input from the user. Don't end your result with questions or offers for further assistance.
Usage:
<attempt_completion>
<result>
Your final result description here
</result>
</attempt_completion>

Example: Requesting to attempt completion with a result and command
<attempt_completion>
<result>
I've updated the CSS, run `open index.html` to see the changes.
</result>
</attempt_completion>
""")
