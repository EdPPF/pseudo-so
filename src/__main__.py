"""Entrypoint do pacote pseudo-so."""

import argparse
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

from .simulation import run_simulation


def _resolve_cli_paths(argv: Sequence[str]) -> Tuple[Path, Path, Path]:
    if argv and all(not arg.startswith("-") for arg in argv):
        if len(argv) not in (2, 3):
            raise SystemExit("Uso: python -m src <processes.txt> <files.txt> [string.txt]")
        return (
            Path(argv[0]),
            Path(argv[1]),
            Path(argv[2]) if len(argv) == 3 else Path("string.txt"),
        )

    parser = argparse.ArgumentParser(description="Pseudo-SO")
    parser.add_argument(
        "--processes",
        type=Path,
        default=Path("processes.txt"),
        help="Caminho para o arquivo de definição de processos (default: processes.txt)",
    )
    parser.add_argument(
        "--files",
        type=Path,
        default=Path("files.txt"),
        help="Caminho para o arquivo de definição de arquivos (default: files.txt)",
    )
    parser.add_argument(
        "--strings",
        type=Path,
        default=Path("string.txt"),
        help="Caminho para o arquivo de strings de referência (default: string.txt)",
    )
    args = parser.parse_args(list(argv))
    return args.processes, args.files, args.strings


def main(argv: List[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    processes, files, strings = _resolve_cli_paths(argv)
    run_simulation(processes, files, strings)


if __name__ == "__main__":
    main()