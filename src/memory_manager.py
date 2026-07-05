"""Memory management with contiguous allocation for real-time and user processes."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MemorySegment:
    """Represents a contiguous block of memory."""

    start: int  # Starting block address
    size: int  # Size in blocks

    @property
    def end(self) -> int:
        """Get the last block address of this segment.

        Returns:
            Last block address (inclusive)
        """
        return self.start + self.size - 1


class MemoryManager:
    """Manages memory allocation with strict separation for real-time and user processes."""

    TOTAL_BLOCKS = 20
    RT_RESERVED = 8  # First 8 frames reserved for real-time processes
    USER_START = RT_RESERVED
    USER_BLOCKS = TOTAL_BLOCKS - RT_RESERVED

    def __init__(self) -> None:
        # RT area: free list for first-fit allocation
        self.rt_free_segments: List[MemorySegment] = [
            MemorySegment(0, self.RT_RESERVED)
        ]
        # User area: free list for first-fit allocation
        self.user_free_segments: List[MemorySegment] = [
            MemorySegment(self.USER_START, self.USER_BLOCKS)
        ]

    def allocate(self, blocks: int, is_real_time: bool) -> Optional[int]:
        """Allocate contiguous memory blocks in the appropriate area."""
        if blocks <= 0:
            return None
        if is_real_time:
            # RT: first-fit allocation in RT area
            for idx, seg in enumerate(self.rt_free_segments):
                if seg.size >= blocks:
                    offset = seg.start
                    seg.start += blocks
                    seg.size -= blocks
                    if seg.size == 0:
                        self.rt_free_segments.pop(idx)
                    return offset
            return None
        # User: first-fit allocation
        for idx, seg in enumerate(self.user_free_segments):
            if seg.size >= blocks:
                offset = seg.start
                seg.start += blocks
                seg.size -= blocks
                if seg.size == 0:
                    self.user_free_segments.pop(idx)
                return offset
        return None

    def free(self, offset: int, blocks: int, is_real_time: bool) -> None:
        """Release memory in the appropriate area."""
        if blocks <= 0:
            return
        if is_real_time:
            # RT area: insert and coalesce
            new_seg = MemorySegment(offset, blocks)
            idx = 0
            while (
                idx < len(self.rt_free_segments)
                and self.rt_free_segments[idx].start < offset
            ):
                idx += 1
            self.rt_free_segments.insert(idx, new_seg)
            self._coalesce_rt()
            return
        # User area: insert and coalesce
        new_seg = MemorySegment(offset, blocks)
        idx = 0
        while (
            idx < len(self.user_free_segments)
            and self.user_free_segments[idx].start < offset
        ):
            idx += 1
        self.user_free_segments.insert(idx, new_seg)
        self._coalesce_user()

    def _coalesce_rt(self) -> None:
        """Merge adjacent free segments in the RT area only."""
        merged: List[MemorySegment] = []
        for seg in sorted(self.rt_free_segments, key=lambda s: s.start):
            if merged and merged[-1].end + 1 == seg.start:
                merged[-1].size += seg.size
            else:
                merged.append(seg)
        self.rt_free_segments = merged

    def _coalesce_user(self) -> None:
        """Merge adjacent free segments in the user area only."""
        merged: List[MemorySegment] = []
        for seg in sorted(self.user_free_segments, key=lambda s: s.start):
            if merged and merged[-1].end + 1 == seg.start:
                merged[-1].size += seg.size
            else:
                merged.append(seg)
        self.user_free_segments = merged

    def reset_rt(self) -> None:
        """Reset RT area (for use when all RT processes have exited)."""
        self.rt_free_segments = [MemorySegment(0, self.RT_RESERVED)]

    def __str__(self) -> str:
        """String representation showing free memory segments for both areas."""
        rt_str = "RT: " + ", ".join(
            f"[{s.start}-{s.end}]" for s in self.rt_free_segments
        )
        user_str = "User: " + ", ".join(
            f"[{s.start}-{s.end}]" for s in self.user_free_segments
        )
        return f"{rt_str} | {user_str}"
