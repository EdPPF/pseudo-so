# Pseudo OS: Uma simulação de Sistema Operacional

Uma implementação simples de um sistema operacional, escrita em Python, composta por Gerenciador de Processos, Gerenciador de Memória, Gerenciador de E/S e Gerenciador de Arquivos.

## Overview

As partes que compões este projeto são descritas como:

- **Gerenciador de Processos**: TODO;
- **Gerenciador de Memória**: TODO;
- **Gerenciador de Recursos de E/S**: Alocação exclusiva de recursos para scanners, impressoras, modems e unidades SATA;
- **File System**: TODO.

## Features

TODO

## Requerimentos

- Python 3.12 ou superior

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/edppf/pseudo-so
cd pseudo-so
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

- WINDOWS:
```bash
.venv\Scripts\Activate.ps1
```

> Pode ser necessario rodar o seguinte comando, que as vezes é executado automaticamente pelo terminal integrado do VS Code:
> 
> `(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& <caminho_para_o_projeto>\pseudo-so\.venv\Scripts\Activate.ps1)`

- Linux/MacOS:
```
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

A simulação precisa de três arquivos de input:

1. **processes.txt**: Definições de processos com cronograma, prioridade e requisitos de recursos;
2. **files.txt**: Estado inicial e operações do sistema de arquivos;
3. **string**: Strings de referência das páginas usadas na execução de cada processo.

### Rodando

```bash
# Usando o módulo dispatcher
python -m src <processes.txt> <files.txt> <string.txt>
```

Por exemplo:

```bash
python -m src tests/default/processes.txt tests/default/files.txt tests/default/string.txt
```

## Estrutura do projeto

TODO

## Formatos dos arquivos de entrada

TODO

## License

PENDING

> This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
