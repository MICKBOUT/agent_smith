import subprocess
from pathlib import Path

IMAGE_NAME = "agent-smith-sandbox:local"


def run_docker_single(args: list[str], code: str = "") -> None:
    build_dir = Path(__file__).resolve().parent / "build_context"

    subprocess.run(
        ["docker", "build", "--quiet", "--tag", IMAGE_NAME, str(build_dir)],
        check=True,
    )

    print("Lancement du conteneur...")
    subprocess.run(
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


if __name__ == "__main__":
    run_docker_single(["math", "--single"], "print('test')")
