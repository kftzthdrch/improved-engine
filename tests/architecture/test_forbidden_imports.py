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
DOMAIN_DIR = os.path.join(BASE, 'app', 'domain')
APP_DIR = os.path.join(BASE, 'app', 'application')


def test_domain_does_not_import_fastapi():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('fastapi'), f"{fp} imports fastapi"

def test_domain_does_not_import_pydantic():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('pydantic'), f"{fp} imports pydantic"

def test_domain_does_not_import_infrastructure():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.infrastructure'), f"{fp} imports infrastructure"

def test_domain_does_not_import_api():
    for fp in get_python_files(DOMAIN_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.api'), f"{fp} imports api"

def test_application_does_not_import_fastapi():
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('fastapi'), f"{fp} imports fastapi"

def test_application_does_not_import_pydantic():
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('pydantic'), f"{fp} imports pydantic"

def test_application_does_not_import_infrastructure():
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.infrastructure'), f"{fp} imports infrastructure"

def test_application_does_not_import_api():
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert not imp.startswith('app.api'), f"{fp} imports api"
