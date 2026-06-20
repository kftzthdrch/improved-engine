import os
import ast
import pytest

FORBIDDEN = ['sqlalchemy', 'alembic', 'sqlite', 'postgres', 'psycopg', 'asyncpg', 'redis', 'pymongo']

BASE = os.path.join(os.path.dirname(__file__), '..', '..')
APP_DIR = os.path.join(BASE, 'app')


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
                imports.append(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.lower())
    return imports


@pytest.mark.parametrize("forbidden", FORBIDDEN)
def test_no_database_imports(forbidden):
    for fp in get_python_files(APP_DIR):
        imports = get_imports(fp)
        for imp in imports:
            assert forbidden not in imp, f"{fp} imports forbidden package: {forbidden}"
