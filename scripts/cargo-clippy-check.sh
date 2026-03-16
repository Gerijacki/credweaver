#!/usr/bin/env bash
export PATH="$HOME/.cargo/bin:$PATH"
exec cargo clippy --manifest-path rust_engine/Cargo.toml -- \
    -D clippy::all \
    -A dead_code \
    -A unused_imports \
    -A unused_variables
