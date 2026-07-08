"""Process Control Block (PCB). Definição de dados - define a estrutura de um processo."""

from dataclasses import dataclass, field
from enum import Enum, auto


class ProcessState(Enum):       
    """Define os estados de um processo."""
    NEW = auto()                # Processo criado
    READY = auto()              # Processo pronto, aguardando a CPU
    RUNNING = auto()            # Processo em execução na CPU
    WAITING = auto()            # Processo bloqueado
    TERMINATED = auto()         # Processo finalizado
    REJECTED = auto()           # Processo rejeitado por violar limites da especificação


@dataclass
class Process:
    
    ## Atributos fixos do processo, lidos do arquivo de entrada
    pid: int                    # Identificação
    arrival_time: int           # Instante em que o processo entra no sistema (ms)
    priority: int               # Prioridade (0: tempo real, 1-3: processos de usuário)
    cpu_time: int               # Tempo total de CPU necessário para concluir (ms)
    memory_blocks: int          # Quantidade de blocos memória necessários
    
    ## Recursos de entrada e saída (E/S)
    printers: int               # Quantidade de impressoras solicitadas
    scanners: int               # Quantidade de scanners solicitados
    modems: int                 # Quantidade de modems solicitados
    sata: int                   # Quantidade de dispositivos SATA solicitados

    reference_string: list[int] = field(default_factory=list)           # String de referência das páginas do processo
    page_faults: int = field(init=False, default=0)                     # Quantidade de faltas de página durante a execução
    
    ## Estado de execução, gerenciado pelo sistema operacional
    remaining_time: int = field(init=False)                             # Tempo restante de CPU
    state: ProcessState = field(init=False, default=ProcessState.NEW)   # Estado atual do processo
    current_queue_level: int = field(init=False)                        # Prioridade dinâmica (1 a 3) para processos de usuário
    waited_time: int = field(init=False, default=0)                     # Tempo de espera nas filas de pronto (aging)
    instructions_executed: int = field(init=False, default=0)           # Quantidade de instruções executadas
    started: bool = field(init=False, default=False)                    # Indica se o processo já foi despachado pela primeira vez
    rejection_reason: str | None = field(init=False, default=None)      # Motivo de rejeição do processo
    admission_wait_reported: bool = field(init=False, default=False)    # Evita repetir avisos de espera na admissão


    def __post_init__(self) -> None:        # Inicializa os atributos calculados após a criação do processo
        self.remaining_time = self.cpu_time
        self.current_queue_level = self.priority if self.priority != 0 else 0


    @property
    def is_real_time(self) -> bool:         # Verifica se o processo é de tempo real (prioridade 0)
        return self.priority == 0


    def needs_resources(self) -> bool:      # Verifica se o processo necessita de algum recurso de E/S
        return any([self.printers, self.scanners, self.modems, self.sata])


    def __str__(self) -> str:               # Representação em texto do processo, utilizada para depuração
        return (
            f"PID={self.pid} P{self.priority} CPU={self.cpu_time} MEM={self.memory_blocks} "
            f"PRN={self.printers} SCN={self.scanners} MDM={self.modems} SATA={self.sata}"
        )
