from textwrap import dedent

EXECUTE_COMMAND_PROMPT = dedent("""
## execute_command
Description: Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. For command chaining, use the appropriate chaining syntax for the user's shell. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Prefer relative commands and paths that avoid location sensitivity for terminal consistency, e.g: `touch ./testdata/example.file`, `dir ./examples/model1/data/yaml`, or `go test ./cmd/front --config ./cmd/front/config.yml`. If directed by the user, you may open a terminal in a different directory by using the `cwd` parameter. When you use this tool, the user will run the command on their terminal, and in the response, the user will provide you the output of the command and any additional information or feedback they want to share. You can use this information to help the user with their task. If the user does not provide the output or feedback, you can ask them for it or any clarifications using the `ask_followup_question` tool.
Parameters:
- command: (required) The CLI command to execute. This should be valid for the current operating system. Ensure the command is properly formatted and does not contain any harmful instructions.
- cwd: (optional) The working directory to execute the command in (default: {pwd}).
- timeout: (optional, in seconds) Use this only for commands that run forever, like running dev servers e.g. 'npm run dev', fastapi, flask, django etc. The user will run the command for this many seconds and then send you the output.

Note:
- Do not try to run 'cd' command to change directory, it will not work as cd state is not preserved. If you wanna run a command in a different directory other than "{pwd}", you need to put that directory in the `cwd` parameter.
- the command will be executed in a non-interactive shell, so make sure the command doesn't require user interaction. If user interaction is must, ask the user via ask_followup_question to manually run the command.


Usage:
<execute_command>
<command>Your command here</command>
<cwd>Working directory path (optional)</cwd>
</execute_command>

Example: Requesting to execute npm run dev
<execute_command>
<command>npm run dev</command>
<timeout>10</timeout>
</execute_command>

Example: Requesting to execute ls in a specific directory if directed
<execute_command>
<command>ls -la</command>
<cwd>/home/user/projects</cwd>
</execute_command>
""")
