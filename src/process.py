"""Process Control Block (PCB) implementation for OS simulation."""

from dataclasses import dataclass, field
from enum import Enum, auto


class ProcessState(Enum):
    """Process states in the simulation lifecycle."""

    NEW = auto()  # Process created but not yet admitted
    READY = auto()  # Process has resources and waiting for CPU
    RUNNING = auto()  # Process currently executing on CPU
    WAITING = auto()  # Process waiting for resources/memory
    TERMINATED = auto()  # Process completed execution


@dataclass
class Process:
    """Process Control Block containing all process information and state.

    Represents a process in the pseudo-OS with its resource requirements,
    scheduling information, and runtime state.
    """

    ## Static process attributes from input file
    pid: int
    arrival_time: int  # Time when process enters the system (ms)
    priority: int  # 0: real-time, 1-3: user processes
    cpu_time: int  # Total CPU time required to complete (ms)
    memory_blocks: int  # Maximum working-set size in frames
    ## I/O resource requirements
    printers: int
    scanners: int
    modems: int
    sata: int
    ## String de referência atrelada ao processo
    reference_string: list[int] = field(default_factory=list)
    page_faults: int = field(init=False, default=0)  # Track page faults during execution
    ## Runtime state - managed by the OS during execution
    remaining_time: int = field(init=False)  # CPU time left to execute
    state: ProcessState = field(init=False, default=ProcessState.NEW)
    current_queue_level: int = field(init=False)  # Dynamic priority 1-3 for user processes
    waited_time: int = field(init=False, default=0)  # Time waiting in ready queues (for aging)
    instructions_executed: int = field(init=False, default=0)  # Track progress
    started: bool = field(init=False, default=False)  # True after first CPU dispatch

    def __post_init__(self) -> None:
        """Initialize computed fields after dataclass creation."""
        self.remaining_time = self.cpu_time
        self.current_queue_level = self.priority if self.priority != 0 else 0

    @property
    def is_real_time(self) -> bool:
        """Check if process is real-time (priority 0).

        Returns:
            True if process has real-time priority
        """
        return self.priority == 0

    def needs_resources(self) -> bool:
        """Check if process requires any I/O resources.

        Returns:
            True if process needs any I/O devices
        """
        return any([self.printers, self.scanners, self.modems, self.sata])

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"PID={self.pid} P{self.priority} CPU={self.cpu_time} MEM={self.memory_blocks} "
            f"PRN={self.printers} SCN={self.scanners} MDM={self.modems} SATA={self.sata}"
        )
