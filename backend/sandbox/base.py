"""The sandbox interface every backend implements, and the limits it enforces."""
import os
from dataclasses import dataclass
from typing import Protocol

TIMED_OUT = {124, 137}  # coreutils `timeout`: 124 when it stops the command, 137 when it has to kill it
MAX_OUTPUT_CHARS = 20_000  # per stream; long build logs keep their end, where errors are


@dataclass(frozen=True)
class Limits:
    # Defaults fit Docker Desktop at 6 CPUs / 6 GB, leaving room for Docker itself; override in .env
    cpus: int = int(os.getenv("SANDBOX_CPUS", "5"))  # cores the container is pinned to
    memory: str = os.getenv("SANDBOX_MEMORY", "4g")
    processes: int = 512
    timeout: int = 600  # seconds per command
    network: bool = False  # only the setup stage gets network


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    seconds: float

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def timed_out(self) -> bool:
        return self.exit_code in TIMED_OUT

    def tail(self, chars: int = 2000) -> str:
        """The end of the output, where build errors and failed assertions are."""
        return (self.stdout + ("\n" + self.stderr if self.stderr else ""))[-chars:]


def clip(text: str) -> str:
    return text if len(text) <= MAX_OUTPUT_CHARS else "[...]\n" + text[-MAX_OUTPUT_CHARS:]


class Sandbox(Protocol):
    def run(self, command: str, timeout: int | None = None) -> CommandResult: ...
    def close(self) -> None: ...
