#!/usr/bin/env bash
# install-hooks.sh — one-time setup for git hooks.
# Run once after cloning: bash scripts/install-hooks.sh
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "🔧 Installing CredWeaver git hooks..."
echo ""

# ── 1. Ensure pre-commit is available ────────────────────────────────────────
if ! command -v pre-commit &>/dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# ── 2. Install pre-commit hook (runs linters on every commit) ────────────────
echo "▶  pre-commit install (pre-commit hook)"
pre-commit install

# ── 3. Install pre-push hook (runs full test suite on push) ──────────────────
HOOKS_DIR="$(git rev-parse --git-dir)/hooks"
echo "▶  Installing pre-push hook → ${HOOKS_DIR}/pre-push"

cp scripts/pre-push "${HOOKS_DIR}/pre-push"
chmod +x "${HOOKS_DIR}/pre-push"

echo ""
echo "✅ Hooks installed successfully!"
echo ""
echo "   pre-commit (on git commit):"
echo "     • ruff lint + format check"
echo "     • mypy type check"
echo "     • cargo fmt check"
echo "     • cargo clippy"
echo ""
echo "   pre-push (on git push):"
echo "     • pytest tests/unit/ tests/integration/"
echo "     • cargo test"
echo ""
echo "   Run all pre-commit checks manually:"
echo "     pre-commit run --all-files"
echo ""
echo "   Skip hooks in emergencies (use sparingly):"
echo "     git commit --no-verify"
echo "     git push  --no-verify"
