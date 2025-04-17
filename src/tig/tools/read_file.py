from typing import Annotated
import os


async def read_file(
    file: Annotated[str, "The file to read, either 'html' or 'css'"],
) -> str:
    """
    Useful for getting the contents of either the html or css file. shows the line numbers, which are used for applying diff.
    """

    try:
        base_dir = "html_resume"
        print(f"\nGetting contents from file: {file}...\n")
        file_to_read = os.path.join(
            base_dir, "resume.html" if file == "html" else "style.css"
        )
        with open(file_to_read, "r") as f:
            contents = f.readlines()
            return "".join([f"{i + 1} | {line}" for i, line in enumerate(contents)])
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {str(e)}. Try again..."
