#!/usr/bin/env bash
export PATH="$HOME/.cargo/bin:$PATH"
exec cargo fmt --manifest-path rust_engine/Cargo.toml -- --check
