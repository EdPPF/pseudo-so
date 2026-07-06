"""Memory management with contiguous allocation for real-time and user processes."""

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# @dataclass
# class MemorySegment:
#     """Represents a contiguous block of memory."""

#     start: int  # Starting block address
#     size: int  # Size in blocks

#     @property
#     def end(self) -> int:
#         """Get the last block address of this segment.

#         Returns:
#             Last block address (inclusive)
#         """
#         return self.start + self.size - 1
    

@dataclass
class ProcessPageTable:
    """Estado de paginação de um processo: páginas em ordem de uso (LRU local) e contador de faltas."""

    pid: int
    max_frames: int
    is_real_time: bool
    resident: OrderedDict = field(default_factory=OrderedDict) # page -> None, início = LRU
    page_faults: int = 0

    # def preload(self, page:int) -> None:
    #     """Pré carga de uma página, antes do processo rodar."""
    #     self.resident[page] = None

    # def reference(self, page:int) -> bool:
    #     """Processa uma entrada da string de referência. Retorna True se houver falha."""
    #     if page in self.resident:
    #         # Atualiza LRU
    #         self.resident.move_to_end(page) # vira a mais recente usada
    #         return False
    #     self.page_faults += 1
    #     if len(self.resident) >= self.max_frames:
    #         # Remove a página menos recentemente usada
    #         self.resident.popitem(last=False)
    #     self.resident[page] = None
    #     return True

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


# Para evitar problemas de alocação por conta de fragmentação interna, usamos contadores Contadores de blocos livres para cada área.
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
        if is_real_time:
            if max_frames > self.rt_frames_free:
                return None
            self.rt_frames_free -= max_frames
        else:
            if max_frames > self.user_frames_free:
                return None
            self.user_frames_free -= max_frames

        page_table = ProcessPageTable(pid=pid, max_frames=max_frames, is_real_time=is_real_time)
        # if first_page is not None:
        #     page_table.preload(first_page)
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

    # def allocate(self, blocks: int, is_real_time: bool) -> Optional[int]:
    #     """Allocate contiguous memory blocks in the appropriate area."""
    #     if blocks <= 0:
    #         return None
    #     if is_real_time:
    #         # RT: first-fit allocation in RT area
    #         for idx, seg in enumerate(self.rt_free_segments):
    #             if seg.size >= blocks:
    #                 offset = seg.start
    #                 seg.start += blocks
    #                 seg.size -= blocks
    #                 if seg.size == 0:
    #                     self.rt_free_segments.pop(idx)
    #                 return offset
    #         return None
    #     # User: first-fit allocation
    #     for idx, seg in enumerate(self.user_free_segments):
    #         if seg.size >= blocks:
    #             offset = seg.start
    #             seg.start += blocks
    #             seg.size -= blocks
    #             if seg.size == 0:
    #                 self.user_free_segments.pop(idx)
    #             return offset
    #     return None

    # def free(self, offset: int, blocks: int, is_real_time: bool) -> None:
    #     """Release memory in the appropriate area."""
    #     if blocks <= 0:
    #         return
    #     if is_real_time:
    #         # RT area: insert and coalesce
    #         new_seg = MemorySegment(offset, blocks)
    #         idx = 0
    #         while (
    #             idx < len(self.rt_free_segments)
    #             and self.rt_free_segments[idx].start < offset
    #         ):
    #             idx += 1
    #         self.rt_free_segments.insert(idx, new_seg)
    #         self._coalesce_rt()
    #         return
    #     # User area: insert and coalesce
    #     new_seg = MemorySegment(offset, blocks)
    #     idx = 0
    #     while (
    #         idx < len(self.user_free_segments)
    #         and self.user_free_segments[idx].start < offset
    #     ):
    #         idx += 1
    #     self.user_free_segments.insert(idx, new_seg)
    #     self._coalesce_user()

    # def _coalesce_rt(self) -> None:
    #     """Merge adjacent free segments in the RT area only."""
    #     merged: List[MemorySegment] = []
    #     for seg in sorted(self.rt_free_segments, key=lambda s: s.start):
    #         if merged and merged[-1].end + 1 == seg.start:
    #             merged[-1].size += seg.size
    #         else:
    #             merged.append(seg)
    #     self.rt_free_segments = merged

    # def _coalesce_user(self) -> None:
    #     """Merge adjacent free segments in the user area only."""
    #     merged: List[MemorySegment] = []
    #     for seg in sorted(self.user_free_segments, key=lambda s: s.start):
    #         if merged and merged[-1].end + 1 == seg.start:
    #             merged[-1].size += seg.size
    #         else:
    #             merged.append(seg)
    #     self.user_free_segments = merged

    # def reset_rt(self) -> None:
    #     """Reset RT area (for use when all RT processes have exited)."""
    #     self.rt_free_segments = [MemorySegment(0, self.RT_RESERVED)]

    # def __str__(self) -> str:
    #     """String representation showing free memory segments for both areas."""
    #     rt_str = "RT: " + ", ".join(
    #         f"[{s.start}-{s.end}]" for s in self.rt_free_segments
    #     )
    #     user_str = "User: " + ", ".join(
    #         f"[{s.start}-{s.end}]" for s in self.user_free_segments
    #     )
    #     return f"{rt_str} | {user_str}"
