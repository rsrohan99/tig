import subprocess
import os


def run_shell_command(
    command: str, cwd: str, timeout_seconds: int = 10, max_lines: int = 50
) -> str:
    """
    Runs a shell command in a specified directory and captures its output.

    For commands expected to run long (like 'npm run dev'), it waits for
    'timeout_seconds'. If the command doesn't finish by then, it captures
    the output generated so far, terminates the process, and returns the
    partial output. It always returns only the last 'max_lines' of the
    captured output (either full or partial).

    Args:
        command: The shell command string to execute.
        cwd: The directory (current working directory) in which to run the command.
        timeout_seconds: The maximum time in seconds to wait for the command.
                         If the command runs longer, its output up to this point
                         is captured, and the process is terminated.
        max_lines: The maximum number of lines from the *end* of the output
                   to return.

    Returns:
        A string containing the last 'max_lines' of the command's combined
        stdout and stderr, or an error message if execution fails.

    Note:
        - Using shell=True can be a security hazard if the command string
          is constructed from untrusted external input. Ensure the command is trusted.
        - Combines stdout and stderr into one output stream.
    """
    output_lines = []
    error_message = None
    returncode = None
    is_timeout = False
    process = None  # Initialize process to None

    try:
        # Basic validation for CWD
        if not os.path.isdir(cwd):
            return f"Error: CWD does not exist or is not a directory: '{cwd}'"

        # Start the process
        # Using text=True (Python 3.7+) automatically handles decoding.
        # stderr=subprocess.STDOUT combines stderr into the stdout stream.
        # Use Popen for non-blocking start and ability to timeout/kill later.
        process = subprocess.Popen(
            command,
            shell=True,  # Often necessary for commands like 'npm run dev' or complex shell syntax
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Capture stderr along with stdout
            text=True,  # Decode output as text
            encoding="utf-8",  # Be explicit about encoding
            errors="replace",  # Handle potential decoding errors gracefully
        )

        # Try to communicate with the process, applying the timeout
        try:
            # communicate() waits for the process to terminate OR the timeout.
            # It reads all output and returns it.
            # If timeout occurs, it kills the process and raises TimeoutExpired.
            stdout_data, _ = process.communicate(timeout=timeout_seconds)
            # If we reach here, the process finished within the timeout.
            returncode = process.returncode

        except subprocess.TimeoutExpired:
            process.kill()
            stdout_data, _ = process.communicate()
            is_timeout = True

        # Process the captured output (full or partial)
        if stdout_data:
            # Strip leading/trailing whitespace and split into lines
            output_lines = stdout_data.strip().splitlines()

    except FileNotFoundError:
        error_message = f"Error: Command or components not found for: '{command}'"
    except NotADirectoryError:
        error_message = f"Error: CWD path exists but is not a directory: '{cwd}'"
    except PermissionError:
        error_message = (
            f"Error: Permission denied to execute command or access CWD '{cwd}'"
        )
    except Exception as e:
        # Catch other potential exceptions during Popen or communicate
        error_message = f"An unexpected error occurred: {type(e).__name__}: {e}"
    finally:
        # Ensure the process is terminated if it somehow still exists
        # (communicate() should handle termination on timeout/completion,
        # but this is an extra safeguard).
        if process and process.poll() is None:  # Check if process is still running
            try:
                process.kill()
                process.wait()  # Wait briefly for resources to be cleaned up
            except Exception as kill_err:
                print(
                    f"Error trying to kill lingering process: {kill_err}"
                )  # Log this, but don't overwrite main error

    # --- Return formatting ---
    if error_message:
        # If an error occurred during setup or execution
        return f"[execute_command for command: '{command}' inside '{cwd}'] Failed to execute command.\nError message: {error_message}\n"
    elif output_lines:
        # If we have output lines (full or partial)
        last_lines = output_lines[-max_lines:]
        combined_output = "\n".join(last_lines)
        return f"[execute_command for command: '{command}' inside '{cwd}'] Result:\n{f'Exit code: {returncode}\n' if returncode is not None else ''}Captured output{f'(After running for {timeout_seconds} seconds)' if is_timeout else ''}:\n<output>\n{combined_output}\n</output>\n"
    else:
        # If the command ran successfully (or timed out) but produced no output
        if process and returncode is not None and returncode != 0:
            # If it finished with an error code but no output was captured
            return f"[execute_command for commane: '{command}' inside '{cwd}'] Command finished with error code {process.returncode}, but no output captured"
        else:
            # If it finished successfully or timed out with genuinely no output
            return f"[execute_command for command: '{command}' inside '{cwd}'] Result:\n{f'Exit code: {returncode}\n' if returncode is not None else ''}No output captured.{f'(After running for {timeout_seconds} seconds)' if is_timeout else ''}\n"
