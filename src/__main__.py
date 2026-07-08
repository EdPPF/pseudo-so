import argparse
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

from .simulation import run_simulation

## Obtém os caminhos dos três arquivos de entrada informados pela linha de comando
def _resolve_cli_paths(argv: Sequence[str]) -> Tuple[Path, Path, Path]:
    parser = argparse.ArgumentParser(
        description="Pseudo-SO",
        epilog="Uso: python -m src <processes.txt> <files.txt> <string.txt>"
    )

    parser.add_argument(
        "processes",
        type=Path,
        help="Caminho para o arquivo de definicao de processos",
    )

    # Define o argumento obrigatório correspondente ao arquivo do sistema de arquivos
    parser.add_argument(
        "files",
        type=Path,
        help="Caminho para o arquivo de definicao de arquivos",
    )

    # Define o argumento obrigatório correspondente ao arquivo de strings de referência
    parser.add_argument(
        "strings",
        type=Path,
        help="Caminho para o arquivo de strings de referencia",
    )
    
    # Lê e valida os argumentos informados
    args = parser.parse_args(list(argv))
    # Retorna os três caminhos informados pelo usuário
    return args.processes, args.files, args.strings

## Função principal que obtém os arquivos de entrada e inicia a simulação
def main(argv: List[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    processes, files, strings = _resolve_cli_paths(argv)
    run_simulation(processes, files, strings)


if __name__ == "__main__":
    main()
