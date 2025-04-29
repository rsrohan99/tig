import subprocess
import sys
import os
import threading
from collections import deque
from typing import Deque

import psutil
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings


# Helper function to run in the reader thread
def _reader_thread_func(
    process: subprocess.Popen,
    output_deque: Deque[str],
    stop_event: threading.Event,
    stream_to_terminal: bool = True,
):
    """Reads output lines, prints them, and stores them in a deque."""
    try:
        # process.stdout should be valid as we set PIPE
        # Use iter to read lines until EOF ('')
        if not process.stdout:
            return
        if stream_to_terminal:
            sys.stdout.write(
                "# Command output:  (press 'x' to terminate running command)\n"
                + "-" * 80
                + "\n"
            )
            sys.stdout.flush()
        for line in iter(process.stdout.readline, ""):
            if stop_event.is_set():
                # print("[Reader Thread] Stop event set, breaking.", file=sys.stderr)
                break

            # line already decoded if text=True in Popen
            line_stripped = line.rstrip()  # Keep original line ending for print

            if stream_to_terminal:
                try:
                    # Write directly to stdout and flush to ensure visibility
                    sys.stdout.write(f"| {line}")
                    sys.stdout.flush()
                except Exception as stream_err:
                    # Handle cases where stdout might be closed or unavailable
                    print(f"[Reader Thread Stream Error] {stream_err}", file=sys.stderr)

            output_deque.append(line_stripped)  # Store line without trailing newline

        if stream_to_terminal:
            sys.stdout.write("-" * 77 + "\n")
            sys.stdout.flush()

        # print("[Reader Thread] Reached EOF or stop event.", file=sys.stderr)

    except ValueError:
        # Can happen if the process closes stdout abruptly after stop_event is set
        # or if Popen failed and process.stdout is None (though caught earlier usually)
        if not stop_event.is_set():
            print(
                "[Reader Thread Error] ValueError (possibly closed pipe)",
                file=sys.stderr,
            )
    except Exception as e:
        # Catch other potential errors during reading
        print(
            f"[Reader Thread Error] An unexpected error occurred: {e}", file=sys.stderr
        )
    finally:
        # print("[Reader Thread] Exiting.", file=sys.stderr)
        # Ensure stdout is closed if Popen didn't handle it (should be automatic)
        if process.stdout and not process.stdout.closed:
            try:
                process.stdout.close()
            except Exception:
                pass  # Ignore errors during cleanup close


def _terminate_process_tree(process: subprocess.Popen):
    """Terminates the process and its children using psutil or platform fallback."""
    pid = process.pid
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        procs_to_terminate = children + [parent]  # Include parent

        # Terminate children first, then parent
        for p in children:
            try:
                # print(f"    Terminating child PID {p.pid} ({p.name()})...", file=sys.stderr)
                p.terminate()
            except psutil.NoSuchProcess:
                # print(f"    Child PID {p.pid} already gone.", file=sys.stderr)
                pass
            except Exception as child_term_err:
                print(
                    f"    Error terminating child {p.pid}: {child_term_err}",
                    file=sys.stderr,
                )

        try:
            # print(f"    Terminating parent PID {parent.pid} ({parent.name()})...", file=sys.stderr)
            parent.terminate()
        except psutil.NoSuchProcess:
            # print(f"    Parent PID {parent.pid} already gone.", file=sys.stderr)
            pass
        except Exception as parent_term_err:
            print(
                f"    Error terminating parent {parent.pid}: {parent_term_err}",
                file=sys.stderr,
            )

        # Wait for graceful termination, then kill leftovers
        _, alive = psutil.wait_procs(procs_to_terminate, timeout=2)

        for p in alive:
            try:
                # print(
                #     f"    Force killing remaining process PID {p.pid} ({p.name()})...",
                #     file=sys.stderr,
                # )
                p.kill()
            except psutil.NoSuchProcess:
                # print(f"    Process PID {p.pid} gone before kill.", file=sys.stderr)
                pass
            except Exception as kill_err:
                print(f"    Error force killing {p.pid}: {kill_err}", file=sys.stderr)

        return

    except psutil.NoSuchProcess:
        pass
        # print(
        #     f"--- Process PID {pid} not found by psutil (already terminated?). ---",
        #     file=sys.stderr,
        # )
        # Fall through to Popen methods just in case Popen object still exists
    except Exception as psutil_err:
        print(
            f"--- An error occurred during psutil termination: {psutil_err}. Falling back... ---",
            file=sys.stderr,
        )


def _terminate_on_keypress(
    process: subprocess.Popen,
    stop_event: threading.Event,
):
    session = PromptSession()
    kb = KeyBindings()

    @kb.add("<any>")
    def _(event):
        # Get the pressed key character
        key = event.key_sequence[0].key
        if key == "x":
            stop_event.set()
            _terminate_process_tree(process)
            try:
                process.wait(timeout=1)  # Allow Popen object to update
            except Exception:
                pass
        event.app.exit()

    try:
        session.prompt("", key_bindings=kb, multiline=False)
        session.app.exit()
    except Exception:
        pass


def run_shell_command(
    command: str, cwd: str, timeout_seconds: int = 3600, max_lines: int = 50
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
    output_deque: Deque[str] = deque(maxlen=max_lines)
    stop_reader_event = threading.Event()
    reader_thread = None
    key_listener_thread = None

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
            bufsize=1,  # Line-buffered
            universal_newlines=True,  # Ensure text mode works correctly           errors="replace",  # Handle potential decoding errors gracefully
        )
        reader_thread = threading.Thread(
            target=_reader_thread_func,
            args=(process, output_deque, stop_reader_event, True),
            daemon=True,  # Allows main program to exit even if thread is stuck (though we join later)
        )
        reader_thread.start()

        # Start a thread to listen for 'x' keypress to terminate the process
        key_listener_thread = threading.Thread(
            target=_terminate_on_keypress,
            args=(
                process,
                stop_reader_event,
            ),
            daemon=True,
        )
        key_listener_thread.start()

        try:
            process.wait(timeout=timeout_seconds)
            returncode = process.returncode

        except subprocess.TimeoutExpired:
            is_timeout = True
            stop_reader_event.set()
            _terminate_process_tree(process)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print(
                    "--- Warning: Process did not update status quickly after termination signal. ---",
                    file=sys.stderr,
                )
            except Exception as wait_err:
                print(
                    f"--- Warning: Error waiting after termination signal: {wait_err} ---",
                    file=sys.stderr,
                )

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
        # Ensure the reader thread is stopped and joined
        if reader_thread and reader_thread.is_alive():
            stop_reader_event.set()
            # print("[Main Thread] Joining reader thread...", file=sys.stderr)
            reader_thread.join(timeout=2.0)  # Wait briefly for reader to finish
            if reader_thread.is_alive():
                print(
                    "[Main Thread] Warning: Reader thread did not exit cleanly.",
                    file=sys.stderr,
                )

    if len(output_deque) == max_lines and max_lines > 0:
        output_lines.append("...")  # Indicate truncation if deque is full

    output_lines.extend(list(output_deque))  # Add lines from deque
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
