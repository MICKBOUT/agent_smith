import unittest

from sandbox import SandboxConfig, Sandbox
import time


class SandboxTests(unittest.TestCase):
    def test_imports(self):
        print("\x1b[92m\n\n[TEST] Import Access\x1b[0m")
        test_content = {
            "import math, re": (["math", "re"], 0),
            "import os": ([], 1),
            "import math": (["functools"], 1),
            "import functools": (["math"], 1),
        }
        for code, content in test_content.items():
            imp, ret = content
            print("Allowed imports:\x1b[34m", code.split(maxsplit=1)[1], "\x1b[0m")
            print("Tested imports:\x1b[34m", ", ".join(imp), "\x1b[0m")
            sandbox = Sandbox(SandboxConfig(authorized_imports=imp), quiet=True)
            self.assertEqual(sandbox.execute(code).returncode, ret)
            print("\x1b[32m - test ok\n\x1b[0m")

    def test_timout(self):
        print("\x1b[92m\n\n[TEST] Timout Limit\x1b[0m", flush=True)
        for i in [1, 2, 3]:
            print(f"Test for limit {i}s, Found: ", end="", flush=True)
            sandbox = Sandbox(
                SandboxConfig(max_execution_time_seconds=i), quiet=True
            )
            before = time.monotonic()
            with self.assertRaises(Exception):
                sandbox.execute("while True: pass")

            self.assertEqual(round(time.monotonic() - before), i)
            print("\x1b[32m", round(time.monotonic() - before, 3), "\x1b[0m")

    def test_memory(self):
        print("\x1b[92m\n\n[TEST] Memory Limit\x1b[0m")
        sandbox_128 = Sandbox(SandboxConfig(max_memory_mb=128), quiet=True)
        sandbox_256 = Sandbox(SandboxConfig(max_memory_mb=256), quiet=True)
        sandbox_512 = Sandbox(SandboxConfig(max_memory_mb=512), quiet=True)

        for sandbox in [sandbox_128, sandbox_256, sandbox_512]:
            target = sandbox.config.max_memory_mb
            for memory in range(0, 1024, 64):
                code = (
                    "chunks = []\n"
                    "total_mb = 0\n"
                    f"for i in range({memory} + 10):\n"
                    "    chunks.append(b'a' * 1_000_000)\n"
                    "    total_mb += 1\n"
                    )

                result = sandbox.execute(code)

                if result.returncode == 0:
                    print(f"{memory}; ", end="", flush=True)
                if result.returncode != 0:
                    print(f"\x1b[32m{memory}")
                    print(result.stderr)

                    print(f"Found {memory} for target {target}!\n\x1b[0m", flush=True)
                    self.assertTrue(target in range(memory - 5, memory + 5))
                    break


if __name__ == "__main__":
    unittest.main()
