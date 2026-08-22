# Contributing to PataNgoma AudioTagger

Thank you for contributing to **PataNgoma**! We welcome bug reports, improvements, provider adapters, and architectural enhancements.

---

## 1. Code of Conduct & Core Philosophy

1. **Determinism Before Intelligence**: AI and fuzzy matching are advisory; audio mutations must be explicit, verified, and reversible.
2. **Safe Automation**: All mutation commands must support `--dry-run` and record snapshots in the audit log.
3. **Pure Domain Models**: Never import Click, Rich, or terminal libraries inside `patangoma.domain` or `patangoma.services`.

---

## 2. Development Setup

We use Astral `uv` for managing dependencies and environments:

```bash
# Clone repository
git clone https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool.git
cd PataNgoma-AudioTagger-tool

# Install all dependencies and setup virtual environment
uv sync --all-groups
```

---

## 3. Contribution Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name` or `fix/your-fix-name`.
2. Implement your changes in the appropriate architectural layer:
   - `src/patangoma/domain/` for pure models and typed exceptions.
   - `src/patangoma/providers/` for metadata provider protocol implementations.
   - `src/patangoma/matching/` for matching logic.
   - `src/patangoma/services/` for application orchestration.
   - `src/patangoma/cli.py` for CLI user interface.
3. Write automated unit and fixture tests in `tests/unit/`.
4. Run formatting and test suites:
   ```bash
   uv run ruff check --fix .
   uv run ruff format .
   uv run pytest --cov=patangoma
   ```
5. Commit using Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).
6. Push and submit a Pull Request targeting `dev` or `main`.
