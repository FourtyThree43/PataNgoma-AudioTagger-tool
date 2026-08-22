# DEVELOPMENT.md — Developer Workflow & Setup Guide

This guide covers local environment setup, dependency management, code formatting, linting, and testing practices for **PataNgoma AudioTagger**.

---

## 1. Prerequisites & Tooling

PataNgoma standardizes on **Python >= 3.10** and Astral **`uv`** for dependency resolution and virtual environment management.

### Installing `uv`
If `uv` is not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 2. Environment Setup

Clone the repository and synchronize the virtual environment:

```bash
git clone https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool.git
cd PataNgoma-AudioTagger-tool

# Install runtime and development dependencies
uv sync
```

This creates a managed `.venv/` directory and locks exact versions in `uv.lock`.

---

## 3. Common Development Commands

All tools should be executed via `uv run` to ensure consistency:

### Linting & Code Formatting
```bash
# Check code style and lint rules
uv run ruff check .

# Automatically apply safe lint fixes
uv run ruff check --fix .

# Check formatting without modifying files
uv run ruff format --check .

# Apply formatting across all files
uv run ruff format .
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=patangoma --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_track.py
```

### Running the CLI
```bash
# Run the entry point directly
uv run patangoma --help
uv run patangoma show path/to/song.mp3
```

---

## 4. Managing Dependencies

All dependencies are declared in `pyproject.toml`. Do not edit `requirements.txt` manually.

- **Add a runtime dependency**:
  ```bash
  uv add <package-name>
  ```
- **Add a development dependency**:
  ```bash
  uv add --group dev <package-name>
  ```
- **Update dependencies & lockfile**:
  ```bash
  uv lock --upgrade
  uv sync
  ```

---

## 5. Testing & Synthetic Audio Fixtures

### Test Directory Structure
```text
tests/
├── conftest.py          # Shared fixtures, temporary directory hooks, mock providers
├── fixtures/            # Synthetic test audio files (mp3, flac, m4a, ogg, wav)
├── unit/                # Fast, isolated unit tests for domain & services
├── integration/         # Provider and audio file mutation integration tests
└── contract/            # Contract tests for MetadataProvider protocol implementations
```

### Guidelines for Audio Fixtures
- Never commit copyrighted music or large audio files to version control.
- Use synthetic silent audio generated with Mutagen/MediaFile for testing tag read/write operations.
- Test edge cases: missing tags, multi-artist strings, invalid unicode, very long strings, and empty ID3 tags.
