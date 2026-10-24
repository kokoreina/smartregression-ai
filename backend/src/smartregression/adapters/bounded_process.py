"""Bounded host-tool subprocesses; workload cleanup remains the caller obligation."""

import subprocess
import threading


class CommandFailure(ValueError):
    """Retain bounded diagnostic bytes for explicit local inspection, never echo by default."""

    def __init__(self, output: bytes) -> None:
        super().__init__("command_failed")
        self.output = output


def bounded_command(
    args: list[str],
    timeout: float,
    cap: int,
    *,
    env: dict[str, str] | None = None,
    merge_stderr: bool = True,
) -> bytes:
    """Drain one merged pipe while bounding retained bytes; kill client on overflow.

    Docker workload cleanup is the caller's finally obligation, also on Ctrl-C.
    """
    data = bytearray()
    overflow = threading.Event()
    with subprocess.Popen(
        args,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if merge_stderr else subprocess.DEVNULL,
    ) as process:

        def consume() -> None:
            assert process.stdout is not None
            while chunk := process.stdout.read(4096):
                if len(data) + len(chunk) > cap:
                    overflow.set()
                    process.kill()
                    break
                data.extend(chunk)

        reader = threading.Thread(target=consume, daemon=True)
        reader.start()
        try:
            process.wait(timeout=timeout)
        except BaseException:
            process.kill()
            process.wait()
            raise
        finally:
            reader.join(timeout=5)
        if overflow.is_set():
            raise ValueError("output_limit")
        if process.returncode:
            raise CommandFailure(bytes(data))
    return bytes(data)
