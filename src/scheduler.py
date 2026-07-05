"""Process scheduler implementing FIFO for real-time processes and multilevel feedback queues for user processes."""

from collections import deque
from typing import Deque, List, Optional

from .memory_manager import MemoryManager
from .process import Process, ProcessState
from .resource_manager import ResourceManager

# Constants for scheduling policy
TIME_QUANTUM = 1  # ms quantum for user processes
AGING_THRESHOLD = 5  # ms wait time before promoting process to higher priority


class Scheduler:
    """Manages process admission, ready queues, dispatching and aging.

    Implements a two-tier scheduling system:
    - Real-time processes (priority 0): FIFO without preemption
    - User processes (priority 1-3): Multilevel feedback queues with aging
    """

    def __init__(self, mem: MemoryManager, res: ResourceManager) -> None:
        """Initialize scheduler with memory and resource managers.

        Args:
            mem: Memory manager for RAM allocation
            res: Resource manager for I/O device allocation
        """
        self.memory = mem
        self.resources = res
        # Admission queue for processes waiting for memory/resources
        self.admission: Deque[Process] = deque()
        # Ready queues
        self.rt_queue: Deque[Process] = deque()  # FIFO for real-time processes
        self.user_queues: List[Deque[Process]] = [
            deque() for _ in range(3)
        ]  # Levels 1-3 for user processes
        # Currently running process
        self.current: Optional[Process] = None

    def add_new_process(self, proc: Process) -> None:
        """Insert a newly arrived process to admission queue.

        Args:
            proc: Process to add (initially in NEW state)
        """
        self.admission.append(proc)

    def try_admit(self) -> None:
        """Attempt to allocate memory/resources for processes in admission queue.

        Moves processes to ready queues if resources are available.
        """
        pending = deque()
        while self.admission:
            proc = self.admission.popleft()
            if self._allocate_resources(proc):
                proc.state = ProcessState.READY
                self._enqueue_ready(proc)
            else:
                # Keep waiting for resources
                pending.append(proc)
        self.admission = pending

    def _allocate_resources(self, proc: Process) -> bool:
        """Attempt to allocate memory and I/O resources for a process.

        Args:
            proc: Process requesting resources

        Returns:
            True if all resources allocated successfully, False otherwise
        """
        # Allocate memory first
        offset = self.memory.allocate(proc.memory_blocks, proc.is_real_time)
        if offset is None:
            return False
        # Real-time processes don't need I/O resources
        if not proc.is_real_time and not self.resources.allocate(
            proc.printers, proc.scanners, proc.modems, proc.sata
        ):
            # Rollback memory allocation if I/O allocation fails
            self.memory.free(offset, proc.memory_blocks, proc.is_real_time)
            return False
        proc.memory_offset = offset
        return True

    def _enqueue_ready(self, proc: Process) -> None:
        """Add process to appropriate ready queue based on priority.

        Args:
            proc: Process to enqueue (must be in READY state)
        """
        if proc.is_real_time:
            self.rt_queue.append(proc)
        else:
            level = proc.current_queue_level - 1  # Convert 1-3 to 0-2 array index
            self.user_queues[level].append(proc)

    def dispatch(self) -> Optional[Process]:
        """Select next process for execution using priority scheduling.

        Real-time processes have absolute priority over user processes.

        Returns:
            Process selected for execution, or None if no process available
        """
        if self.current and self.current.state == ProcessState.RUNNING:
            # Current process still running
            return self.current
        # Select next process (RT processes have absolute priority)
        if self.rt_queue:
            self.current = self.rt_queue.popleft()
        else:
            # Check user queues from highest to lowest priority
            for q in self.user_queues:
                if q:
                    self.current = q.popleft()
                    break
            else:
                self.current = None
        if self.current:
            self.current.state = ProcessState.RUNNING
            self.current.waited_time = 0  # Reset wait time when scheduled
            self._print_dispatch(self.current)
            print(f"process {self.current.pid} =>")
            # Print start message for newly started processes
            if hasattr(self.current, "_just_started"):
                print(f"    P{self.current.pid} STARTED")
                delattr(self.current, "_just_started")
        return self.current

    def tick(self) -> None:
        """Simulate one millisecond of CPU time and perform scheduling operations."""
        # 1) Try to admit waiting processes
        self.try_admit()
        # 2) Apply aging to user processes waiting in ready queues
        for lvl, q in enumerate(self.user_queues):
            for _ in range(len(q)):
                proc = q.popleft()
                proc.waited_time += 1
                # Promote process if it has waited long enough and isn't at highest priority
                if proc.waited_time >= AGING_THRESHOLD and proc.current_queue_level > 1:
                    proc.current_queue_level -= 1  # Higher priority (lower number)
                    proc.waited_time = 0
                self._enqueue_ready(proc)
        # 3) Dispatch next process if needed
        proc = self.dispatch()
        if proc is None:
            return  # CPU idle
        # 4) Execute one time quantum
        if proc.is_real_time:
            # Real-time: run until completion (no preemption)
            proc.remaining_time -= 1
            proc.instructions_executed += 1
            print(f"    P{proc.pid} instruction {proc.instructions_executed}")
            finished = proc.remaining_time == 0
        else:
            # User process: execute up to time quantum
            exec_time = min(TIME_QUANTUM, proc.remaining_time)
            proc.remaining_time -= exec_time
            proc.instructions_executed += exec_time
            for i in range(exec_time):
                print(
                    f"    P{proc.pid} instruction {proc.instructions_executed - exec_time + i + 1}"
                )
            finished = proc.remaining_time == 0
        if finished:
            print(f"    P{proc.pid} return SIGINT")
            self._terminate_process(proc)
            self.current = None
        else:
            # Time slice expired for user process - preempt and requeue
            if not proc.is_real_time:
                proc.state = ProcessState.READY
                # Demote process to lower priority queue if not already at lowest
                if proc.current_queue_level < 3:
                    proc.current_queue_level += 1
                self._enqueue_ready(proc)
                self.current = None

    def _terminate_process(self, proc: Process) -> None:
        """Clean up resources when process terminates.

        Args:
            proc: Process to terminate
        """
        proc.state = ProcessState.TERMINATED

        # Release memory for all processes
        self.memory.free(proc.memory_offset or 0, proc.memory_blocks, proc.is_real_time)
        # Release resources (user processes only)
        if not proc.is_real_time:
            self.resources.free(proc.printers, proc.scanners, proc.modems, proc.sata)

    @staticmethod
    def _print_dispatch(proc: Process) -> None:
        """Print dispatcher information when process is selected for execution.

        Args:
            proc: Process being dispatched
        """
        print("dispatcher =>")
        print(f"    PID: {proc.pid}")
        print(f"    frames: {proc.memory_blocks}")
        print(f"    priority: {proc.priority}")
        print(f"    time: {proc.remaining_time}")
        print(f"    printers: {proc.printers}")
        print(f"    scanners: {proc.scanners}")
        print(f"    modems: {proc.modems}")
        print(f"    drives: {proc.sata}")
