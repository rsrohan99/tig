from textwrap import dedent

OBJECTIVES_PROMPT = dedent("""
====
OBJECTIVE

- Break task into steps.
- Use tools to accomplish each step.
- Wait for user confirmation after each tool use.
- Only use attempt_completion if all the steps for the given task are done and the task is complete. Do a lot of thinking inside <thinking>...</thinking> tags to evaluate current progress.
- Use attempt_completion when task is complete.
""")
