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
COPY cupp/ ./cupp/
COPY rust_engine/src/ ./rust_engine/src/
COPY cupp.yaml ./

# Build wheel (compiles Rust + packages Python)
RUN maturin build --release --out /dist

# Stage 2: Runtime image
FROM python:3.12-slim AS runtime

LABEL maintainer="CUPP v2 Contributors"
LABEL description="CUPP v2 — Advanced Password Wordlist Generator"
LABEL org.opencontainers.image.source="https://github.com/Gerijacki/cupp_v2"

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash cupp
USER cupp
WORKDIR /home/cupp

# Copy wheel from builder and install
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir --user /tmp/*.whl && rm /tmp/*.whl

# Copy default config and profiles
COPY --chown=cupp:cupp cupp.yaml ./
COPY --chown=cupp:cupp profiles/ ./profiles/

# Output volume
VOLUME ["/output"]

ENV PATH="/home/cupp/.local/bin:${PATH}"

ENTRYPOINT ["cupp"]
CMD ["--help"]
