"""The local sandbox: a Docker container (via llm-sandbox) with the target's workspace mounted.

Every attempt gets a fresh container. Inside it there is no network, a read-only system, an
unprivileged user with no extra capabilities, capped CPU, memory and processes, and a timeout on every
command. Hidden data (e.g. test labels) is mounted read-only only for grading runs."""
import shlex
import time
from pathlib import Path
import docker
from docker.types import Mount
from llm_sandbox import SandboxSession
from sandbox.base import CommandResult, Limits, clip

BASE_IMAGE = "lume-sandbox:base"
DOCKERFILE_DIR = Path(__file__).parent
WORKDIR, HIDDEN_DIR = "/work", "/hidden"
KILL_AFTER = 5  # seconds between asking a timed-out command to stop and killing it


def build_base_image(client: docker.DockerClient | None = None) -> str:
    """Build the base image once (compilers, Python, hyperfine, ripgrep); later runs reuse it."""
    client = client or docker.from_env()
    client.images.build(path=str(DOCKERFILE_DIR), tag=BASE_IMAGE, rm=True)
    return BASE_IMAGE


def runtime_config(workspace: Path, limits: Limits, hidden: Path | None, setup: bool) -> dict:
    mounts = [Mount(WORKDIR, str(workspace.resolve()), type="bind")]
    if (workspace / ".git").is_dir():  # attempts are git commits: code inside can't rewrite them
        mounts.append(Mount(f"{WORKDIR}/.git", str((workspace / ".git").resolve()), type="bind", read_only=True))
    if hidden:
        mounts.append(Mount(HIDDEN_DIR, str(hidden.resolve()), type="bind", read_only=True))
    config = {
        # No secrets: nothing from the host's environment. No bytecode caches written into the workspace.
        "mounts": mounts, "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
        "mem_limit": limits.memory, "memswap_limit": limits.memory,  # equal: no swap on top of the cap
        # Pinned cores, not a CPU-time quota: programs see exactly this many cores (so thread pools
        # aren't oversubscribed) and repeated timings vary less
        "cpuset_cpus": f"0-{max(int(limits.cpus), 1) - 1}", "pids_limit": limits.processes,
        "network_mode": "bridge" if limits.network else "none",
    }
    if not setup:  # the setup stage installs dependencies, so only it may write outside /work as root
        config.update(user="lume", read_only=True, tmpfs={"/tmp": "size=1g", "/home/lume": "size=256m"},
                      cap_drop=["ALL"], security_opt=["no-new-privileges"])
    return config


class DockerSandbox:
    def __init__(self, workspace, image: str = BASE_IMAGE, limits: Limits = Limits(), hidden=None,
                 setup: bool = False, save_as: str | None = None):
        """setup=True runs as root with the given network setting so dependencies can be installed;
        save_as then saves the container as a new image for the task's attempts."""
        self.limits = limits
        self.session = SandboxSession(
            backend="docker", image=image, lang="python", workdir=WORKDIR, skip_environment_setup=True,
            keep_template=True, commit_container=bool(save_as), commit_image_tag=save_as,
            runtime_configs=runtime_config(Path(workspace), limits, Path(hidden) if hidden else None, setup))
        self.session.open()

    def run(self, command: str, timeout: int | None = None) -> CommandResult:
        seconds = timeout or self.limits.timeout
        wrapped = f"timeout -k {KILL_AFTER} {seconds} sh -c {shlex.quote(command)}"
        started = time.monotonic()
        output = self.session.execute_command(wrapped, workdir=WORKDIR)
        return CommandResult(command=command, exit_code=output.exit_code, stdout=clip(output.stdout),
                             stderr=clip(output.stderr), seconds=round(time.monotonic() - started, 3))

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
