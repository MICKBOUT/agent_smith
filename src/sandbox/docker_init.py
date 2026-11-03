import subprocess
from pathlib import Path

IMAGE_NAME = "agent-smith-sandbox:local"


class Container:
    """
    Class for executing python code in an isolated
    environnement with docker
    """
    def __init__(self) -> None:
        """First build of the container"""
        build_dir = Path(__file__).resolve().parent / "build_context"

        subprocess.run(
            ["docker", "build", "--quiet", "--tag", IMAGE_NAME, str(build_dir)],
            check=True,
        )

    def run(self, args: list[str], code: str) -> subprocess.CompletedProcess:
        """
        this method can execute a single bloc of python code
        in a isolated environnment.

        Args:
            args: list of arguments for the child process.
            code: the code to be executed.

        Return:
            CompletedProcess: the result of the process.
        """
        print("Lancement du conteneur...")
        result = subprocess.run(
            [
                "docker", "run", "--rm", "--interactive",
                "--memory=512m", "--memory-swap=512m", "--network=none",
                IMAGE_NAME, "python", "worker.py", *args,
            ],
            input=code,
            text=True,
            capture_output=True,
            check=True,
        )

        return result

    def run_interactive(self, args: list[str]) -> None:
        print("Lancement du conteneur...")
        print("non implemente")
