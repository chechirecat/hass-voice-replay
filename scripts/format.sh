#!/usr/bin/env bash
# Development helper script for formatting and linting

set -e

echo "🔧 Running ruff formatter..."
ruff format .

echo "🔍 Running ruff linter..."
ruff check . --fix

echo "✅ Code formatting and linting complete!"
echo ""
echo "💡 Tip: To run this automatically on every commit, install pre-commit:"
echo "   pip install pre-commit"
echo "   pre-commit install"