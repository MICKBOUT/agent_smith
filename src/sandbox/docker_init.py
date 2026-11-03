import subprocess
from pathlib import Path

IMAGE_NAME = "agent-smith-sandbox:local"


class Container:
    def __init__(self) -> None:
        build_dir = Path(__file__).resolve().parent / "build_context"

        subprocess.run(
            ["docker", "build", "--quiet", "--tag", IMAGE_NAME, str(build_dir)],
            check=True,
        )

    def run(self, args: list[str], code: str) -> None:
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
