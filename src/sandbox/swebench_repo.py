import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def load_swebench_repository(image: str) -> Iterator[Path]:
    """Load a SWE-bench image's /testbed checkout into a temporary workspace."""
    workspace = Path(tempfile.mkdtemp(prefix="agent-smith-swebench-"))
    container_id = ""
    previous_testbed = os.environ.get("TESTBED_PATH")

    try:
        subprocess.run(["docker", "pull", image], check=True)
        container_id = subprocess.check_output(
            ["docker", "create", image],
            text=True,
        ).strip()
        subprocess.run(
            ["docker", "cp", f"{container_id}:/testbed/.", str(workspace)],
            check=True,
        )
        os.environ["TESTBED_PATH"] = str(workspace)
        yield workspace
    finally:
        if previous_testbed is None:
            os.environ.pop("TESTBED_PATH", None)
        else:
            os.environ["TESTBED_PATH"] = previous_testbed
        if container_id:
            subprocess.run(
                ["docker", "rm", container_id],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        shutil.rmtree(workspace, ignore_errors=True)
