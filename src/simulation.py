from pathlib import Path
from typing import List, Optional, Tuple

from .file_system import FileSystem

from .memory_manager import MemoryManager
from .process import Process, ProcessState
from .resource_manager import ResourceManager
from .scheduler import Scheduler

MAX_PROCESSES = 1000

## Cria um objeto Process a partir dos dados lidos do arquivo
def _build_process(
    pid: int,
    arrival: int,
    priority: int,
    cpu_time: int,
    blocks: int,
    printer: int,
    scanner: int,
    modem: int,
    sata: int,
) -> Process:
    
    # Inicializa o PCB do processo
    return Process(
        pid=pid,
        arrival_time=arrival,
        priority=priority,
        cpu_time=cpu_time,
        memory_blocks=blocks,
        printers=printer,
        scanners=scanner,
        modems=modem,
        sata=sata,
    )

## Valida se os dados de entrada de um processo são permitidos
def _validate_process_fields(
    line_number: int,
    priority: int,
    arrival: int,
    cpu_time: int,
    frames: int,
    printer: int,
    scanner: int,
    modem: int,
    sata: int,
) -> None:
    if priority not in (0, 1, 2, 3):    # Verifica se a prioridade é válida
        raise ValueError(f"Linha {line_number}: prioridade deve estar entre 0 e 3")
    if arrival < 0:                     # Tempo de chegada não pode ser negativo
        raise ValueError(f"Linha {line_number}: tempo de inicializacao negativo")
    if cpu_time <= 0:                   # Processo precisa de tempo de CPU positivo
        raise ValueError(f"Linha {line_number}: tempo de processador deve ser positivo")
    if frames <= 0:                     # Processo precisa ocupar pelo menos um frame
        raise ValueError(f"Linha {line_number}: conjunto de trabalho deve ter ao menos 1 frame")
    if min(printer, scanner, modem, sata) < 0:  # Recursos solicitados não podem ser negativos
        raise ValueError(f"Linha {line_number}: requisicoes de recursos nao podem ser negativas")

    # Define o limite de memória conforme o tipo do processo
    frame_limit = MemoryManager.RT_RESERVED if priority == 0 else MemoryManager.USER_RESERVED
    if frames > frame_limit:            # Impede processos de ultrapassarem a área reservada de memória
        process_type = "tempo real" if priority == 0 else "usuario"
        raise ValueError(
            f"Linha {line_number}: processo de {process_type} solicita {frames} frames, "
            f"mas o limite da area reservada e {frame_limit}"
        )
   
    # Processos de tempo real não utilizam dispositivos de E/S
    if priority == 0 and any((printer, scanner, modem, sata)):
        raise ValueError(f"Linha {line_number}: processo de tempo real nao pode requisitar E/S")
    # Verifica se a quantidade de recursos solicitada existe no sistema
    if printer > ResourceManager.TOTAL_PRINTERS:
        raise ValueError(f"Linha {line_number}: requisicao de impressoras excede o total disponivel")
    if scanner > ResourceManager.TOTAL_SCANNERS:
        raise ValueError(f"Linha {line_number}: requisicao de scanners excede o total disponivel")
    if modem > ResourceManager.TOTAL_MODEMS:
        raise ValueError(f"Linha {line_number}: requisicao de modems excede o total disponivel")
    if sata > ResourceManager.TOTAL_SATA:
        raise ValueError(f"Linha {line_number}: requisicao de SATA excede o total disponivel")

## Lê o arquivo de processos e cria os objetos Process
def parse_processes(path: Path) -> List[Process]:
    processes: List[Process] = []
    with path.open() as file:
        pid = 0  # A sequência de PIDs começa em 0, de acordo com a especificação
        for line_number, line in enumerate(file, 1):    # Percorre cada linha do arquivo
            line = line.strip()                         # Remove espaços e quebras de linha
            if not line or line.startswith("#"):        # Ignora linhas vazias e comentários
                continue    
            if len(processes) >= MAX_PROCESSES:         # Limita quantidade de processos
                raise ValueError(f"O arquivo de processos excede o limite de {MAX_PROCESSES} processos")
            parts = [part.strip() for part in line.split(",")]  # Divide os campos separados por vírgula
            if len(parts) != 8:                         # Cada processo deve possuir 8 campos
                raise ValueError(f"Linha {line_number}: processo deve conter 8 campos")
            try:
                values = list(map(int, parts))          # Converte os valores para inteiro
            except ValueError as exc:
                raise ValueError(f"Linha {line_number}: todos os campos do processo devem ser inteiros") from exc
            # Separa os campos do processo
            (
                arrival,
                priority,
                cpu_time,
                blocks,
                printer,
                scanner,
                modem,
                sata,
            ) = values
            # Confere se os valores são válidos
            _validate_process_fields(
                line_number,
                priority,
                arrival,
                cpu_time,
                blocks,
                printer,
                scanner,
                modem,
                sata,
            )
            # Cria o processo e adiciona na lista
            processes.append(
                _build_process(
                    pid,
                    arrival,
                    priority,
                    cpu_time,
                    blocks,
                    printer,
                    scanner,
                    modem,
                    sata,
                )
            )
            pid += 1                                    # Próximo processo recebe próximo PID

    return processes                                    # Retorna todos os processos criados

## Lê o arquivo do sistema de arquivos
## Retorna o estado inicial do disco e operações futuras
def parse_files(path: Path) -> Tuple[FileSystem, List[Tuple[int, int, str, int]]]:
    with path.open() as file:
        lines = []
        for line in file:                               # Remove linhas vazias e comentários
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
    if len(lines) < 2:                                  # Arquivo precisa ter cabeçalho
        raise ValueError("files.txt sem header!")

    blocks = int(lines[0])                              # Primeiro campo: quantidade de blocos do disco
    n_existing = int(lines[1])                          # Segundo campo: quantidade de arquivos existentes
    # Validação do disco
    if blocks <= 0:
        raise ValueError("Quantidade de blocos do disco deve ser positiva")
    if n_existing < 0:
        raise ValueError("Quantidade de segmentos ocupados nao pode ser negativa")
    # Verifica se existem todos os arquivos declarados
    if len(lines) < n_existing + 2:
        raise ValueError("files.txt possui menos segmentos iniciais do que o declarado")

    idx = 2
    # Guarda arquivos que já existem no disco
    existing: List[Tuple[str, int, int]] = []

    # Lê arquivos iniciais
    for _ in range(n_existing):
        parts = list(map(str.strip, lines[idx].split(",")))
        if len(parts) != 3:
            raise ValueError(f"Arquivo inválido: {lines[idx]}")

        name, start, size = parts[0], int(parts[1]), int(parts[2])
        existing.append((name, start, size))
        idx += 1

    # Cria sistema de arquivos e carrega arquivos existentes
    fs = FileSystem(blocks)
    fs.load_existing(existing)

    operations: List[Tuple[int, int, str, int]] = []
    while idx < len(lines):
        parts = list(map(str.strip, lines[idx].split(",")))
        if len(parts) < 3:
            raise ValueError(f"Linha de operacao invalida: {lines[idx]}")

        pid = int(parts[0])
        opcode = int(parts[1])
        filename = parts[2]
        if pid < 0:
            raise ValueError(f"Linha de operacao invalida: PID negativo em {lines[idx]}")
        if opcode not in (0, 1):
            raise ValueError(f"Linha de operacao invalida: opcode deve ser 0 ou 1 em {lines[idx]}")
        if opcode == 0:
            if len(parts) != 4:
                raise ValueError(f"Linha de criacao invalida: {lines[idx]}")
            size = int(parts[3])
            if size <= 0:
                raise ValueError(f"Linha de criacao invalida: tamanho deve ser positivo em {lines[idx]}")
        else:
            if len(parts) != 3:
                raise ValueError(f"Linha de remocao invalida: {lines[idx]}")
            size = 0
        operations.append((pid, opcode, filename, size))
        idx += 1

    return fs, operations

## Lê o arquivo de strings de referência das páginas
## Retorna uma lista de strings de referência por processo
def parse_reference_strings(path: Path) -> List[List[int]]:
    references: List[List[int]] = []
    with path.open() as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            references.append([int(part.strip()) for part in line.split(",") if part.strip()])
    return references

## Formata uma sequência de blocos de disco para exibição
def _format_block_range(start: int, size: int) -> str:
    blocks = list(range(start, start + size))
    if not blocks:
        return ""
    if len(blocks) == 1:
        return str(blocks[0])
    return ", ".join(str(block) for block in blocks[:-1]) + f" e {blocks[-1]}"

## Executa a parte de processos usando o scheduler real quando disponível
def _drive_process_execution(processes: List[Process]) -> None:
    memory_manager = MemoryManager()
    resource_manager = ResourceManager()
    scheduler = Scheduler(memory_manager, resource_manager)
    time = 0

    while True:
        for process in [p for p in processes if p.arrival_time == time]:
            scheduler.add_new_process(process)

        scheduler.tick()
        finished = sum(1 for process in processes if process.state == ProcessState.TERMINATED)
        if (
            finished == len(processes)
            and not scheduler.admission
            and not scheduler.rt_queue
            and all(not queue for queue in scheduler.user_queues)
            and scheduler.current is None
        ):
            break
        time += 1

## Executa as operações do sistema de arquivos
def _run_filesystem_operations(
    processes: List[Process],
    fs: FileSystem,
    operations: List[Tuple[int, int, str, int]],
) -> None:
    print("Sistema de arquivos =>")
    process_by_pid = {process.pid: process for process in processes}

    for index, (pid, opcode, filename, size) in enumerate(operations, 1):
        process = process_by_pid.get(pid)
        if process is None:
            print(f"    Operação {index} => Falha")
            print(f"    O processo {pid} não existe.")
            continue

        if opcode == 0:
            success = fs.create(pid, process.is_real_time, filename, size)
            if success:
                print(f"    Operação {index} => Sucesso")
                entry = fs.files[filename]
                print(
                    f"    O processo {pid} criou o arquivo {filename} "
                    f"(blocos {_format_block_range(entry.start, entry.size)})."
                )
            else:
                print(f"    Operação {index} => Falha")
                if filename in fs.files:
                    print(f"    O processo {pid} não pode criar o arquivo {filename} porque ele já existe.")
                else:
                    print(f"    O processo {pid} não pode criar o arquivo {filename} (falta de espaço).")
            continue

        success = fs.delete(pid, process.is_real_time, filename)
        if success:
            print(f"    Operação {index} => Sucesso")
            print(f"    O processo {pid} deletou o arquivo {filename}.")
        else:
            print(f"    Operação {index} => Falha")
            if filename not in fs.files:
                print(f"    O processo {pid} não pode deletar o arquivo {filename} porque ele não existe.")
            else:
                print(f"    O processo {pid} não pode deletar o arquivo {filename} porque não é o proprietário.")

## Executa a simulação do pseudo-SO na ordem esperada pela especificação
def run_simulation(procs: Path, files: Path, strings: Optional[Path] = None) -> None:
    strings = strings or Path("string.txt")

    processes = parse_processes(procs)
    fs, operations = parse_files(files)
    reference_strings = parse_reference_strings(strings)
    if len(reference_strings) != len(processes):
        raise ValueError(
            "O arquivo de strings de referencia deve conter exatamente uma linha por processo"
        )

    # Associa string de referencia direto ao seu respectivo processo
    for process, sequence in zip(processes, reference_strings):
        process.reference_string = sequence

    # Escalonador processa o LRU na admissão
    _drive_process_execution(processes)
    # Roda operações do sistema de arquivos após encerramento da CPU
    _run_filesystem_operations(processes, fs, operations)

    print("Mapa de ocupação do disco:")
    fs.dump()

    print("Número de Faltas de Páginas por processo:")
    for process in processes:
        print(f"P{process.pid} = {process.page_faults} faltas de páginas")
