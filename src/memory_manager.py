"""Memory management with contiguous allocation for real-time and user processes."""

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
    

@dataclass
class ProcessPageTable:
    """Estado de paginação de um processo: páginas em ordem de uso (LRU local) e contador de faltas."""

    pid: int
    max_frames: int
    is_real_time: bool
    resident: OrderedDict = field(default_factory=OrderedDict) # page -> None, início = LRU
    page_faults: int = 0

    def process_reference_string(self, ref_string: List[int]) -> int:
        """Processa uma string de referência e retorna o número de faltas de página (LRU local)."""
        if not ref_string:
            return 0
        
        # Pré carga da primeira página
        first_page = ref_string[0]
        self.resident[first_page] = None

        # Processa o restante da string
        for page in ref_string[1:]:
            if page in self.resident:
                self.resident.move_to_end(page) # vira a mais recente usada
            else:
                self.page_faults += 1
                if len(self.resident) >= self.max_frames:
                    self.resident.popitem(last=False)
                self.resident[page] = None
        return self.page_faults


# Para evitar problemas de alocação por conta de fragmentação interna, usamos contadores contadores de blocos livres para cada área.
class MemoryManager:
    """Manages memory allocation with strict separation for real-time and user processes."""

    TOTAL_BLOCKS = 20
    RT_RESERVED = 8  # First 8 frames reserved for real-time processes
    USER_RESERVED = 12
    USER_START = RT_RESERVED
    USER_BLOCKS = TOTAL_BLOCKS - RT_RESERVED

    def __init__(self) -> None:
        self.rt_frames_free = self.RT_RESERVED
        self.user_frames_free = self.USER_RESERVED
        self.page_tables: Dict[int, ProcessPageTable] = {}

    def admit_process(
            self, pid: int, is_real_time: bool,
            max_frames: int, first_page: Optional[int] = None
    ) -> Optional[ProcessPageTable]:
        """Reserva max_frames na área correta. Retorna a PageTable se houver espaço."""
        if max_frames <= 0:
            return None

        if is_real_time:
            if max_frames > self.rt_frames_free:
                return None
            self.rt_frames_free -= max_frames
        else:
            if max_frames > self.user_frames_free:
                return None
            self.user_frames_free -= max_frames

        page_table = ProcessPageTable(pid=pid, max_frames=max_frames, is_real_time=is_real_time)
        self.page_tables[pid] = page_table
        return page_table
    
    def release_process(self, pid: int) -> None:
        """Libera os frames de um processo encerrado."""
        table = self.page_tables.pop(pid, None)
        if table:
            if table.is_real_time:
                self.rt_frames_free += table.max_frames
            else:
                self.user_frames_free += table.max_frames
