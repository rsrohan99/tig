from textwrap import dedent

TOOLS_GUIDELINES_PROMPT = dedent("""
====
Guidelines

- Choose the right tool for the task.
- Use one tool at a time.
- Format tool use correctly.
- Wait for user confirmation after each tool use.
- Don’t assume tool success; wait for user feedback.
- NEVER write imcomplete code e.g. write the full class or function code instead of just adding a comment like "Login logic goes here". Never do that.
- For user interfaces, make them intuitive, beautiful and user-friendly using Material UI.
====
""")
