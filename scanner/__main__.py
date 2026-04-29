"""Entry point: ``python -m scanner <subcommand>``.

Delegates to the Click group in :mod:`scanner.cli`. The wrapper
``_main()`` is referenced by ``pyproject.toml``'s ``[project.scripts]``
so ``scanner`` becomes a console script after ``pip install -e .`` /
``uv sync``.
"""
from scanner.cli import cli


def _main() -> None:
    cli()


if __name__ == "__main__":
    _main()
