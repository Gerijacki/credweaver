# syntax=docker/dockerfile:1
# Stage 1: Rust + Python build environment
FROM python:3.12-slim AS builder

# Install Rust and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential pkg-config libssl-dev git \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Copy dependency files first for layer caching
COPY pyproject.toml ./
COPY rust_engine/Cargo.toml rust_engine/Cargo.lock* ./rust_engine/

# Install Python deps
RUN pip install --no-cache-dir maturin pydantic pyyaml typer rich

# Copy source
COPY README.md ./
COPY credweaver/ ./credweaver/
COPY rust_engine/src/ ./rust_engine/src/
COPY credweaver.yaml ./

# Build wheel (compiles Rust + packages Python)
RUN maturin build --release --out /dist

# Stage 2: Runtime image
FROM python:3.12-slim AS runtime

LABEL maintainer="CredWeaver Contributors"
LABEL description="CredWeaver — Advanced Credential Wordlist Generator"
LABEL org.opencontainers.image.source="https://github.com/Gerijacki/credweaver"

# Install runtime deps and the wheel as root → system site-packages.
# Doing this before USER switch avoids all --user / PYTHONNOUSERSITE path issues.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,from=builder,source=/dist,target=/dist \
    pip install --no-cache-dir /dist/*.whl

# Drop to non-root user for runtime
RUN useradd --create-home --shell /bin/bash credweaver
USER credweaver
WORKDIR /home/credweaver

# Copy default config and profiles
COPY --chown=credweaver:credweaver credweaver.yaml ./
COPY --chown=credweaver:credweaver profiles/ ./profiles/

# Output volume
VOLUME ["/output"]

ENTRYPOINT ["credweaver"]
CMD ["--help"]
