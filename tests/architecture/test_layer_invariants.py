"""Architecture tests enforcing structural layer boundaries and invariants."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_UI_MODULES = {
    "click",
    "rich",
    "InquirerPy",
    "textual",
    "ttkbootstrap",
    "tkinter",
}


def _extract_imported_modules(file_path: Path) -> set[str]:
    """Parse python file and extract all top-level imported module names."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def _extract_full_imports(file_path: Path) -> set[str]:
    """Parse python file and extract all imported module paths."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _has_sys_exit_calls(file_path: Path) -> list[int]:
    """Check if AST contains direct calls to sys.exit or exit()."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Attribute) and node.func.attr == "exit")
            or (isinstance(node.func, ast.Name) and node.func.id in ("exit", "quit"))
        ):
            violations.append(node.lineno)
    return violations


def test_domain_layer_has_no_ui_imports():
    """Invariant 1: No UI packages imported in domain modules."""
    domain_dir = Path(__file__).parents[2] / "src" / "patangoma" / "domain"
    for py_file in domain_dir.glob("*.py"):
        imported = _extract_imported_modules(py_file)
        forbidden = imported.intersection(FORBIDDEN_UI_MODULES)
        assert not forbidden, (
            f"Domain file {py_file.name} imports forbidden UI modules: {forbidden}"
        )


def test_application_layer_has_no_ui_imports():
    """Invariant 2: No UI packages imported in application services or core facade."""
    app_dir = Path(__file__).parents[2] / "src" / "patangoma" / "application"
    for py_file in app_dir.rglob("*.py"):
        imported = _extract_imported_modules(py_file)
        forbidden = imported.intersection(FORBIDDEN_UI_MODULES)
        assert not forbidden, (
            f"Application file {py_file.name} imports forbidden UI modules: {forbidden}"
        )


def test_plugins_have_no_ui_imports():
    """Invariant 5: Plugins never depend on frontends or UI packages."""
    plugins_dir = Path(__file__).parents[2] / "src" / "patangoma" / "plugins"
    for py_file in plugins_dir.rglob("*.py"):
        imported = _extract_imported_modules(py_file)
        forbidden = imported.intersection(FORBIDDEN_UI_MODULES)
        assert not forbidden, (
            f"Plugin file {py_file.name} imports forbidden UI modules: {forbidden}"
        )


def test_domain_and_application_have_no_sys_exit():
    """Invariant 3: No sys.exit() in Domain or Application layers."""
    base_dir = Path(__file__).parents[2] / "src" / "patangoma"
    for layer in ("domain", "application", "plugins"):
        layer_dir = base_dir / layer
        if layer_dir.exists():
            for py_file in layer_dir.rglob("*.py"):
                violations = _has_sys_exit_calls(py_file)
                assert not violations, (
                    f"File {py_file} contains sys.exit() on lines {violations}"
                )


def test_application_has_no_concrete_plugin_imports():
    """Application layer must only interact with PluginRegistry/CapabilityRegistry and never import concrete plugins."""
    app_dir = Path(__file__).parents[2] / "src" / "patangoma" / "application"
    forbidden_subpackages = (
        "patangoma.plugins.metadata",
        "patangoma.plugins.download",
        "patangoma.plugins.media",
        "patangoma.plugins.artwork",
        "patangoma.plugins.export",
        "patangoma.plugins.import_",
        "patangoma.providers.musicbrainz",
        "patangoma.providers.spotify",
        "patangoma.providers.deezer",
        "patangoma.providers.discogs",
        "patangoma.providers.itunes",
        "patangoma.providers.acoustid",
        "patangoma.providers.lyrics",
    )
    for py_file in app_dir.rglob("*.py"):
        imports = _extract_full_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_subpackages:
                assert not imp.startswith(forbidden), (
                    f"Application file {py_file.name} directly imports concrete plugin '{imp}'"
                )
