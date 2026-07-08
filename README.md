# Pseudo OS: Uma simulação de Sistema Operacional

Uma implementação simples de um sistema operacional, escrita em Python, composta por Gerenciador de Processos, Gerenciador de Memória, Gerenciador de E/S e Gerenciador de Arquivos.

## Overview

As partes que compões este projeto são descritas como:

- **Gerenciador de Processos**: Responsável pela criação, admissão, escalonamento e finalização dos processos. Implementa filas multinível para processos de usuário, fila FIFO para processos de tempo real, quantum, preempção, aging e controle dos estados dos processos;
- **Gerenciador de Memória**: Gerencia a alocação e liberação de memória para os processos, mantendo áreas reservadas para processos de tempo real e de usuário. Também simula paginação utilizando o algoritmo LRU para contabilização das faltas de página;
- **Gerenciador de Recursos de E/S**: Alocação exclusiva de recursos para scanners, impressoras, modems e unidades SATA;
- **File System**: Simula um sistema de arquivos baseado em blocos, permitindo carregar arquivos existentes, criar e remover arquivos, controlar proprietários e gerenciar o mapa de ocupação do disco.

## Features

- Escalonamento de processos por múltiplas filas de prioridade;
- Fila FIFO exclusiva para processos de tempo real;
- Quantum e preempção para processos de usuário;
- Mecanismo de aging para evitar starvation;
- Gerenciamento de memória com áreas reservadas para processos de tempo real e usuário;
- Simulação de paginação utilizando o algoritmo LRU;
- Contabilização de faltas de página por processo;
- Gerenciamento exclusivo de recursos de E/S;
- Simulação de sistema de arquivos com criação e remoção de arquivos;
- Exibição do mapa final de ocupação do disco.

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

```
Directory structure:
└── ./
    ├── README.md
    ├── requirements.txt
    ├── src/
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── file_system.py
    │   ├── memory_manager.py
    │   ├── process.py
    │   ├── resource_manager.py
    │   ├── scheduler.py
    │   └── simulation.py
    └── tests/
```

## Formatos dos arquivos de entrada

TODO
