# Lume's base sandbox image: compilers, Python, git and the measuring tools, no project code.
# Each task's own dependencies are installed on top of it once, in a setup stage with network.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build pkg-config git ca-certificates \
        python3 python3-pip python3-venv hyperfine ripgrep coreutils \
    && rm -rf /var/lib/apt/lists/*
# Code runs as an unprivileged user, never root
RUN useradd --create-home --uid 1000 lume
USER lume
WORKDIR /work
