import ast
import os
import pytest


def get_python_files(base_dir: str) -> list[str]:
    files = []
    for root, _, filenames in os.walk(base_dir):
        for f in filenames:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
    return files


def get_imports(filepath: str) -> list[str]:
    with open(filepath, encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


BASE = os.path.join(os.path.dirname(__file__), '..', '..')
INFRA_DIR = os.path.join(BASE, 'app', 'infrastructure')


def test_infrastructure_does_not_import_api():
    for fp in get_python_files(INFRA_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.api'), f"{fp} imports api from infrastructure"

def test_infrastructure_does_not_import_composition():
    for fp in get_python_files(INFRA_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.composition'), f"{fp} imports composition from infrastructure"
