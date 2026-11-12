import subprocess

from pathlib import Path
from uuid import uuid4

from sandbox import SandboxError

IMAGE_NAME = "agent-smith-sandbox:local"
CONTROL_DIRECTORY = "/run/sandbox-control"
CONTROL_SOCKET = f"{CONTROL_DIRECTORY}/sandbox.sock"


class Container:
    """
    Class for executing python code in an isolated
    environnement with docker
    """

    MSG = "\033[34mLoading of container...\033[0m"

    def __init__(self) -> None:
        """First build of the container"""
        build_dir = Path(__file__).resolve().parent / "build_context"

        subprocess.run(
            ["docker", "build", "--quiet", "--tag", IMAGE_NAME, str(build_dir)],
            check=True,
        )

    def run(self, args: list[str], timeout: int, max_memory: int, code: str) -> subprocess.CompletedProcess:
        """
        this method can execute a single bloc of python code
        in a isolated environnment.

        Args:
            args: list of arguments for the child process.
            timeout: the timout limit for the process.
            max_memory: limit of memory which can be allocate.
            code: the code to be executed.

        Return:
            CompletedProcess: the result of the process.
        """

        print(self.MSG)

        result = subprocess.run(
            [
                "docker", "run", "--rm", "--interactive",
                f"--memory={max_memory}m", f"--memory-swap={max_memory}m", "--network=none",
                IMAGE_NAME, "python", "worker.py", *args,
            ],
            input=code,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout
        )

        return result

    def run_interactive(
        self,
        args: list[str],
        control_directory: Path,
        memory_mb: int,
        allowed_directories: list[str],
    ) -> tuple[subprocess.Popen[bytes], str]:
        """
        Start one persistent container for an interactive REPL session.
        
        Args:
            args: arguments for the child process.
            control_directory: the unix socket location.
            memory_mb: the limit of memory it can be allocated.
            allowed_directories: list of allowed directories
        
        Return:
            the process with the name of the container.
            
        Raises
            ValueError: if the memory_mb value zero or negative.
        """

        if memory_mb <= 0:
            raise ValueError("max_memory_mb must be greater than zero")

        container_name = f"agent-smith-repl-{uuid4().hex[:12]}"

        command = [
            "docker", "run",
            "--rm",  # delete instant the old container.
            "--name", container_name,
            "--memory", f"{memory_mb}m",
            "--memory-swap", f"{memory_mb}m",  # the limit of swap + memory !!!!
            "--network=none",
            "--read-only",
            "--pids-limit", "64",  # to avoid fork bomb
            "--cap-drop=ALL",  # to remove all privillege
            "--security-opt=no-new-privileges",
            "--user", "65534:65534",  # its for set the user as nobody/nogroup
            "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--mount",
            (
                "type=bind,"
                f"source={control_directory.resolve()},"
                f"target={CONTROL_DIRECTORY}"
            ),
        ]

        for directory in allowed_directories:
            configured_directory = Path(directory).expanduser()
            if not configured_directory.is_absolute():
                raise SandboxError(
                    f"Allowed directory must be absolute: {directory}"
                )

            host_directory = configured_directory.resolve()
            if not host_directory.is_dir():
                raise SandboxError(
                    f"Allowed directory does not exist: {directory}"
                )
            command.extend(
                [
                    "--mount",
                    (
                        "type=bind,"
                        f"source={host_directory},"
                        f"target={directory},readonly"
                    ),
                ]
            )

        command.extend(
            [IMAGE_NAME, "python", "-B", "-u", "worker.py", *args]
        )

        print(self.MSG)
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
        )
        return process, container_name

    @staticmethod
    def stop_interactive(
        process: subprocess.Popen[bytes],
        container_name: str,
        force: bool = False,
    ) -> None:
        """
        Stop the named container if its REPL session is still running.

        Args:
            process: the process to be stopped
            container_name the name of the container to be stopped.
            force: force flag
        """
        if process.poll() is not None:
            return

        if not force:
            try:
                process.wait(timeout=2)
                return
            except subprocess.TimeoutExpired:
                pass

        subprocess.run(
            ["docker", "kill", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
