import os

ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"


def print_intro(mode: str, auto_approve: bool = False) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print("🐯 Tig - AI coding agent")
    print(f"\nRunning in '{mode}' mode. Available modes: 'architect', 'code'.")
    if auto_approve:
        print(
            f"\n{ANSI_RED}[IMPORTANT!]{ANSI_RESET} Auto-approve mode is enabled. All actions will be executed without confirmation."
        )
    print(
        "\nGive Tig a task to do. Type '/exit' to quit, '/mode <mode_name>' to switch modes.\n"
    )
