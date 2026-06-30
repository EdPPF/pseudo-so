# Pseudo OS: Uma simulação de Sistema Operacional

Uma implementação simples de um sistema operacional, escrita em Python, composta por Gerenciador de Processos, Gerenciador de Memória, Gerenciador de E/S e Gerenciador de Arquivos.

## Overview

As partes que compões este projeto são descritas como:

- **Gerenciador de Processos**: Agendamento de filas de prioridade multinível com FIFO para processos em tempo real e filas de feedback para processos de usuário;
- **Gerenciador de Memória**: Alocação de memória contígua com espaços de endereçamento protegidos;
- **Gerenciador de Recursos de E/S**: Alocação exclusiva de recursos para scanners, impressoras, modems e unidades SATA;
- **File System**: Alocação de arquivos contíguos com algoritmo first-fit.

## Features

- **Agendamento de Prioridade Dupla**: Processos em tempo real (prioridade 0) com agendamento FIFO e processos de usuário com filas de feedback multinível
- **Proteção de Memória**: Sistema de memória de 1024 blocos com 64 blocos reservados para processos em tempo real
- **Gerenciamento de Recursos**: Alocação exclusiva de dispositivos de E/S sem preempção
- **Operações de Arquivos**: Operações de criação e exclusão com permissões específicas do processo
- **Testes Abrangentes**: Testes de validação com comparação da saída esperada

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

A simulação precisa de dois arquivos de input:

1. **processes.txt**: Definições de processos com cronograma, prioridade e requisitos de recursos;
2. **files.txt**:  Estado inicial e operações do sistema de arquivos.

### Rodando

```bash
# Usando o módulo dispatcher
python -m src.dispatcher <processes.txt> <files.txt>

# Ou então
python -m src.os_simulation --processes <processes.txt> --files <files.txt>
```

Por exemplo:

```bash
python -m src.dispatcher assets/test_basic_specification/processes.txt assets/test_basic_specification/files.txt
```

## Testes

Para rodar os testes:

```bash
python -m pytest
```

A pasta `tests/` possui:
- **Teste unitários**: Para módulos individuais;
- **Testes de validação**: Compare os resultados da simulação com os resultados esperados da pasta `assets/`.

## Estrutura do projeto

```
pseudo-so/
├── src/
│   ├── dispatcher.py          # Main process dispatcher
│   ├── os_simulation.py       # Simulation entry point
│   ├── scheduler.py           # Process scheduling logic
│   ├── memory_manager.py      # Memory allocation management
│   ├── resource_manager.py    # I/O resource allocation
│   ├── file_system.py         # File system operations
│   └── process.py             # Process data structures
├── assets/                    # Test cases with expected outputs
├── tests/                     # Unit and validation tests (see Testing section)
└── README.md
```

## Formatos dos arquivos de entrada

### processes.txt
```
<start_time>, <priority>, <cpu_time>, <memory_blocks>, <printer>, <scanner>, <modem>, <disk>
```

### files.txt
```
<disk_blocks>
<occupied_segments>
<file_name>, <start_block>, <block_count>
...
<process_id>, <operation>, <file_name>, [<size_if_create>]
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
