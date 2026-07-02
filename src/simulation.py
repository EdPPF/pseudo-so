"""Módulo principal que orquestra scheduling dos processos e operações do file system."""

from pathlib import Path
from typing import List, Optional, Tuple

from .file_system import FileSystem

from .memory_manager import MemoryManager
from .process import Process, ProcessState
from .resource_manager import ResourceManager
from .scheduler import Scheduler


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


def parse_processes(path: Path) -> List[Process]:
    """Lê processes.txt e retorna uma lista de objetos Process."""
    processes: List[Process] = []
    with path.open() as file:
        pid = 0  # A sequência de PIDs começa em 0, de acordo com a especificação.
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            (
                arrival,
                priority,
                cpu_time,
                blocks,
                printer,
                scanner,
                modem,
                sata,
            ) = map(int, map(str.strip, line.split(",")))
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
            pid += 1

    return processes


def parse_files(path: Path) -> Tuple[FileSystem, List[Tuple[int, int, str, int]]]:
    """Lê files.txt e retorna um objeto FileSystem e uma lista de operações."""
    with path.open() as file:
        lines = [line.strip() for line in file if line.strip() and not line.startswith("#")]
    if len(lines) < 2:
        raise ValueError("files.txt sem header!")

    blocks = int(lines[0])
    n_existing = int(lines[1])
    idx = 2
    existing: List[Tuple[str, int, int]] = []
    for _ in range(n_existing):
        parts = list(map(str.strip, lines[idx].split(",")))
        if len(parts) != 3:
            raise ValueError(f"Arquivo inválido: {lines[idx]}")

        name, start, size = parts[0], int(parts[1]), int(parts[2])
        existing.append((name, start, size))
        idx += 1

    fs = FileSystem(blocks)
    fs.load_existing(existing)

    operations: List[Tuple[int, int, str, int]] = []
    while idx < len(lines):
        parts = list(map(str.strip, lines[idx].split(",")))
        if len(parts) not in (3, 4):
            raise ValueError(f"Linha de operação inválida: {lines[idx]}")

        pid = int(parts[0])
        opcode = int(parts[1])
        filename = parts[2]
        size = int(parts[3]) if opcode == 0 else 0
        operations.append((pid, opcode, filename, size))
        idx += 1

    return fs, operations


def parse_reference_strings(path: Path) -> List[List[int]]:
    """Lê string.txt e retorna uma lista de strings de referência por processo."""
    references: List[List[int]] = []
    with path.open() as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            references.append([int(part.strip()) for part in line.split(",") if part.strip()])
    return references


def _format_block_range(start: int, size: int) -> str:
    blocks = list(range(start, start + size))
    if not blocks:
        return ""
    if len(blocks) == 1:
        return str(blocks[0])
    return ", ".join(str(block) for block in blocks[:-1]) + f" e {blocks[-1]}"


def _print_dispatcher_message(process: Process) -> None:
    print("dispatcher =>")
    print(f"    PID: {process.pid}")
    print(f"    frames: {process.memory_blocks}")
    print(f"    priority: {process.priority}")
    print(f"    time: {process.cpu_time}")
    print(f"    printers: {process.printers}")
    print(f"    scanners: {process.scanners}")
    print(f"    modems: {process.modems}")
    print(f"    drives: {process.sata}")


def _drive_process_execution(processes: List[Process]) -> None:
    """Executa a parte de processos usando o scheduler real quando disponível."""
    memory_manager = MemoryManager()
    resource_manager = ResourceManager()
    scheduler = Scheduler(memory_manager, resource_manager)
    time = 0

    while True:
        for process in [p for p in processes if p.arrival_time == time]:
            setattr(process, "_just_started", True)
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


def _simulate_page_faults(processes: List[Process], references: List[List[int]]) -> List[int]:
    if len(references) != len(processes):
        raise ValueError("string.txt deve ter uma linha de referência para cada processo.")

    faults: List[int] = []
    for process, sequence in zip(processes, references):
        partition_capacity = 8 if process.is_real_time else 12
        capacity = max(1, min(process.memory_blocks, partition_capacity))
        if not sequence:
            faults.append(0)
            continue

        frames = [sequence[0]]
        last_used = {sequence[0]: 0}
        page_faults = 0

        for tick, page in enumerate(sequence[1:], start=1):
            if page in frames:
                last_used[page] = tick
                continue

            page_faults += 1
            if len(frames) >= capacity:
                lru_page = min(frames, key=lambda candidate: last_used.get(candidate, -1))
                frames.remove(lru_page)
                last_used.pop(lru_page, None)

            frames.append(page)
            last_used[page] = tick

        faults.append(page_faults)

    return faults


def run_simulation(procs: Path, files: Path, strings: Optional[Path] = None) -> None:
    """Executa a simulação do pseudo-SO na ordem esperada pela especificação."""
    strings = strings or Path("string.txt")

    processes = parse_processes(procs)
    fs, operations = parse_files(files)
    reference_strings = parse_reference_strings(strings)

    _drive_process_execution(processes)
    _run_filesystem_operations(processes, fs, operations)

    print("Mapa de ocupação do disco:")
    fs.dump()

    page_faults = _simulate_page_faults(processes, reference_strings)
    print("Número de Faltas de Páginas por processo:")
    for process, faults in zip(processes, page_faults):
        print(f"P{process.pid} = {faults} faltas de páginas")
