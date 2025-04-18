from textwrap import dedent

TOOLS_FORMATTING_PROMPT = dedent("""
<task>
{task}
</task>

<environment_details>
# Current Time
{current_time}

# Current Mode
{current_mode}


# Current Workspace Directory ({pwd}) Files
{pwd_files}
</environment_details>
""")
