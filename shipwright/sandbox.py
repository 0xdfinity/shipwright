"""Filesystem and process sandbox for the agent. Every path the model touches
is resolved and must stay inside the project root."""
from __future__ import annotations

import subprocess
from pathlib import Path


class SandboxError(Exception):
    pass


class Sandbox:
    def __init__(self, root: str | Path, test_timeout: int = 60):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise SandboxError(f"project root does not exist: {self.root}")
        self.test_timeout = test_timeout

    def resolve(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            raise SandboxError(f"path escapes project root: {rel}")
        return p

    def list_files(self, max_files: int = 300) -> list[str]:
        out = []
        for p in sorted(self.root.rglob("*")):
            if p.is_file() and not any(part in {".git", "__pycache__", ".pytest_cache"} for part in p.parts):
                out.append(str(p.relative_to(self.root)))
                if len(out) >= max_files:
                    break
        return out

    def read_file(self, rel: str, max_chars: int = 20000) -> str:
        p = self.resolve(rel)
        if not p.is_file():
            raise SandboxError(f"no such file: {rel}")
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]

    def write_file(self, rel: str, content: str) -> str:
        p = self.resolve(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {rel} ({len(content)} chars)"

    def run_tests(self) -> dict:
        """Run pytest inside the project root. Returns exit code and trimmed output."""
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
                cwd=self.root, capture_output=True, text=True, timeout=self.test_timeout,
            )
            output = (proc.stdout + proc.stderr)[-6000:]
            return {"passed": proc.returncode == 0, "exit_code": proc.returncode, "output": output}
        except subprocess.TimeoutExpired:
            return {"passed": False, "exit_code": -1, "output": f"tests timed out after {self.test_timeout}s"}
