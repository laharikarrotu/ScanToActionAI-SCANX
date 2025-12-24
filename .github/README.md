# GitHub Actions Workflows

This directory contains CI/CD workflows for automated testing and code quality checks.

## Workflows

- **backend-tests.yml** - Runs backend unit tests
- **frontend-tests.yml** - Runs frontend type checks, linting, and builds
- **integration-tests.yml** - Runs integration tests
- **code-quality.yml** - Runs code quality checks (Black, Flake8, Mypy, ESLint, TypeScript)

## IDE Linter Warnings

**IMPORTANT**: If you see IDE linter warnings about "Unable to resolve action" or "Context access might be invalid", these are **FALSE POSITIVES** and can be safely ignored.

### Why These Warnings Appear

1. **"Unable to resolve action"** - Your IDE cannot resolve GitHub Actions locally (like `actions/checkout@v4`), but these actions are valid and will work correctly when the workflow runs on GitHub.

2. **"Context access might be invalid: GEMINI_API_KEY"** - This is an IDE warning about accessing GitHub secrets context. The syntax is correct and will work on GitHub.

### Verification

These workflows are tested and working on GitHub. The warnings only appear in your local IDE and do not affect workflow execution.

### Suppressing Warnings

If your IDE supports it, you can:
- Add `.github/workflows/` to your IDE's ignore list for YAML linting
- Configure your IDE to ignore GitHub Actions-specific warnings
- Use the `.vscode/settings.json` file in this directory (if using VS Code)

## Running Workflows Locally

To test workflows locally, use [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run a workflow
act -j test
```

