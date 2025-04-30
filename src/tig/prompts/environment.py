import platform
import os
from datetime import datetime
from tzlocal import get_localzone

from textwrap import dedent

SYSTEM_INFO_REMINDER_PROMPT = dedent("""
====
SYSTEM INFORMATION

Operating System: {os}
Default Shell: {shell}
Home Directory: {home_dir}
Current Workspace Directory: {pwd}

Current Time: {current_time}

The Current Workspace Directory is the active project directory, and is therefore the default directory for all tool operations.

The main task you are trying to accomplish is:
<task>
{task}
</task>

Only attempt_completion if all the steps for the above task are done and the task is complete. Do a lot of thinking inside <thinking>...</thinking> tags to evaluate current progress.
====""")


def get_environment_reminder_prompt(task: str):
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
    return SYSTEM_INFO_REMINDER_PROMPT.format(
        os=os_info,
        shell=default_shell,
        home_dir=home_dir,
        pwd=current_dir,
        current_time=formatted_time,
        task=task,
    )
