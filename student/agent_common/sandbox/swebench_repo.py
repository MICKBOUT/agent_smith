import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def load_swebench_repository(image: str) -> Iterator[Path]:
    """Load a SWE-bench image's /testbed checkout into a temporary workspace."""
    workspace = Path(tempfile.mkdtemp(prefix="agent-smith-swebench-"))
    source_container_id = ""
    task_container_id = ""
    previous_testbed = os.environ.get("TESTBED_PATH")
    previous_container = os.environ.get("SWEBENCH_CONTAINER_ID")

    try:
        image_exists = subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0
        if not image_exists:
            subprocess.run(["docker", "pull", image], check=True)

        source_container_id = subprocess.check_output(
            ["docker", "create", image],
            text=True,
        ).strip()
        subprocess.run(
            ["docker", "cp", f"{source_container_id}:/testbed/.", str(workspace)],
            check=True,
        )

        # Keep one task container alive for the whole agent run. MCP tools edit
        # the host checkout, which is mounted here at the benchmark's /testbed.
        name = f"agent-smith-swebench-{uuid.uuid4().hex[:12]}"
        task_container_id = subprocess.check_output(
            [
                "docker", "run", "--detach", "--name", name,
                "--volume", f"{workspace}:/testbed",
                "--workdir", "/testbed",
                "--entrypoint", "sh", image,
                "-c", "while :; do sleep 3600; done",
            ],
            text=True,
        ).strip()
        os.environ["TESTBED_PATH"] = str(workspace)
        os.environ["SWEBENCH_CONTAINER_ID"] = task_container_id
        yield workspace
    finally:
        if previous_testbed is None:
            os.environ.pop("TESTBED_PATH", None)
        else:
            os.environ["TESTBED_PATH"] = previous_testbed
        if previous_container is None:
            os.environ.pop("SWEBENCH_CONTAINER_ID", None)
        else:
            os.environ["SWEBENCH_CONTAINER_ID"] = previous_container
        for container_id in (task_container_id, source_container_id):
            if not container_id:
                continue
            subprocess.run(
                ["docker", "rm", "--force", container_id],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        shutil.rmtree(workspace, ignore_errors=True)
