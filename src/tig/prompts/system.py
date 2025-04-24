import os
import platform
from datetime import datetime
from tzlocal import get_localzone

from tig.tools import list_files
from tig.modes import MODES

from tig.prompts.tools_formatting import TOOLS_FORMATTING_PROMPT
from tig.prompts.tools_guidelines import TOOLS_GUIDELINES_PROMPT
from tig.prompts.rules import RULES_PROMPT
from tig.prompts.system_info import SYSTEM_INFO_PROMPT
from tig.prompts.objectives import OBJECTIVES_PROMPT

from tig.prompts.tools.read_file import READ_FILE_TOOL_PROMPT
from tig.prompts.tools.search_files import SEARCH_FILES_PROMPT
from tig.prompts.tools.list_files import LIST_FILES_PROMPT
from tig.prompts.tools.list_code_definitions import LIST_CODE_DEFINITION_NAMES_PROMPT
from tig.prompts.tools.apply_diff import APPLY_DIFF_PROMPT
from tig.prompts.tools.write_to_file import WRITE_TO_FILE_PROMPT
from tig.prompts.tools.execute_command import EXECUTE_COMMAND_PROMPT
from tig.prompts.tools.ask_followup_question import ASK_FOLLOWUP_QUESTIONS_PROMPT
from tig.prompts.tools.attempt_completion import ATTEMPT_COMPLETION_PROMPT


def get_system_prompt(
    mode: str,
    task: str,
) -> str:
    os_info = platform.system()  # Returns the OS name (e.g., 'Linux', 'Darwin', etc.)
    default_shell = os.getenv("SHELL")  # The environment variable for default shell
    home_dir = os.path.expanduser("~")  # Expands to the current user's home directory
    current_dir = os.getcwd()  # Gets the current working directory
    local_timezone = get_localzone()
    current_time = datetime.now(local_timezone)
    timezone_name = local_timezone.key
    formatted_time = current_time.strftime(
        f"%m/%d/%Y, %I:%M:%S %p ({timezone_name}, GMT%z)"
    )
    cwd_files_list = list_files(
        {
            "path": current_dir,
            "recursive": True,
        }
    )
    current_mode = MODES[mode]
    system_prompt = ""
    system_prompt += current_mode["role"] + "\n"
    system_prompt += TOOLS_FORMATTING_PROMPT.format() + "\n"
    system_prompt += "\nTools\n" + "\n"
    system_prompt += READ_FILE_TOOL_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += SEARCH_FILES_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += LIST_FILES_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += LIST_CODE_DEFINITION_NAMES_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += APPLY_DIFF_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += WRITE_TO_FILE_PROMPT.format(pwd=current_dir) + "\n"
    if mode == "code":
        system_prompt += EXECUTE_COMMAND_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += ASK_FOLLOWUP_QUESTIONS_PROMPT.format() + "\n"
    system_prompt += ATTEMPT_COMPLETION_PROMPT.format() + "\n\n"
    system_prompt += TOOLS_GUIDELINES_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += RULES_PROMPT.format(pwd=current_dir) + "\n"
    system_prompt += (
        SYSTEM_INFO_PROMPT.format(
            os=os_info,
            shell=default_shell,
            home_dir=home_dir,
            pwd=current_dir,
            current_time=formatted_time,
        )
        + "\n"
    )
    if current_mode["mode_specific_instructions"]:
        system_prompt += f"\nMode Specific Instructions\n{current_mode['mode_specific_instructions']}\n"
    system_prompt += OBJECTIVES_PROMPT.format() + "\n"
    system_prompt += (
        f"Project Directory ({current_dir}) Files: \n{cwd_files_list}\n====\n"
    )
    system_prompt += f"\n<task>\n{task}\n</task>\n"
    return system_prompt
