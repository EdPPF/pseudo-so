from dataclasses import dataclass, field
from enum import Enum, auto

## Define os estados do processo
class ProcessState(Enum):       
    NEW = auto()                # Processo criado
    READY = auto()              # Processo pronto, aguardando a CPU
    RUNNING = auto()            # Processo em execução na CPU
    WAITING = auto()            # Processo bloqueado
    TERMINATED = auto()         # Processo finalizado


@dataclass      # gera automaticamente métodos comuns
## Representa um processo, funcionando como PCB (Process Control Block)
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
    current_queue_level: int = field(init=False)                        # Nível atual da fila de prioridade dinâmica (0 para tempo real, 1-3 para usuários)
    waited_time: int = field(init=False, default=0)                     # Tempo de espera nas filas de pronto (aging)
    instructions_executed: int = field(init=False, default=0)           # Quantidade de instruções executadas
    started: bool = field(init=False, default=False)                    # Indica se o processo já foi despachado pela primeira vez

    ## Inicializa os atributos calculados após a criação do processo
    def __post_init__(self) -> None:     
        self.remaining_time = self.cpu_time                             # Inicializa o tempo restante de CPU com o tempo total informado no arquivo
        self.current_queue_level = self.priority if self.priority != 0 else 0   # Define a fila inicial conforme a prioridade original do processo


    @property   # permite acessar como atributo de leitura
    ## Verifica se o processo é de tempo real (prioridade 0)
    def is_real_time(self) -> bool: 
        return self.priority == 0

    ## Verifica se o processo necessita de algum recurso de E/S
    def needs_resources(self) -> bool: 
        return any([self.printers, self.scanners, self.modems, self.sata])

    ## Representação em texto do processo, utilizada para depuração
    def __str__(self) -> str:
        return (
            f"PID={self.pid} P{self.priority} CPU={self.cpu_time} MEM={self.memory_blocks} "
            f"PRN={self.printers} SCN={self.scanners} MDM={self.modems} SATA={self.sata}"
        )
