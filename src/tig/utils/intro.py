import os


def print_intro(mode: str) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print("🐯 Tig - AI coding agent")
    print(f"\nRunning in '{mode}' mode. Available modes: 'architect', 'code'.")
    print(
        "\nGive Tig a task to do. Type '/exit' to quit, '/mode <mode_name>' to switch modes.\n"
    )
