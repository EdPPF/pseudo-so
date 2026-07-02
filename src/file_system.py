from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass # Dataclass é usada para simplificar a criação de classes que são principalmente usadas para armazenar dados
class FileEntry:
    """Um arquivo armazenado no disco por meio de alocação contígua."""
    filename: str
    start: int
    size: int
    owner_pid: int # 0 para system files

    def __str__(self) -> str:
        """String que representa a alocação do arquivo."""
        return f"{self.filename} [{self.start}:{self.start + self.size - 1}] (size: {self.size}) (owner: {self.owner_pid})"
    

class FileSystem:
    """Sistema de arquivos com alocação contígua.
    Alocação por meio de First Fit.
    
    Suporta Criação e Deleção com permissões de acesso para processos de usuário e real-time."""

    def __init__(self, total_blocks: int) -> None:
        self.total_blocks = total_blocks
        self.files: Dict[str, FileEntry] = {}  # Mapeia nomes de arquivos para suas entradas
        self.free_segments: List[Tuple[int, int]] = [(0, total_blocks)]  # Lista de segmentos livres (start, size)

    def load_existing(self, entries: List[Tuple[str, int, int]]) -> None:
        """Carrega arquivos existentes no sistema de arquivos."""
        for name, start, size in entries:
            if not self._is_space_available(start, size):
                raise RuntimeError(f"Espaço insuficiente para carregar o arquivo existente {name}\nEm: {start}")
            self._occupy(start, size)
            self.files[name] = FileEntry(name, start, size, owner_pid=0)

    def create(self, pid: int, is_real_time: bool, filename: str, size: int) -> bool:
        if size <= 0 or filename in self.files:
            return False

        start = self._first_fit(size)
        if start is None:
            return False

        self._occupy(start, size)
        self.files[filename] = FileEntry(filename, start, size, owner_pid=pid)
        return True

    def delete(self, pid: int, is_real_time: bool, filename: str) -> bool:
        entry = self.files.get(filename)
        if entry is None:
            return False

        if not is_real_time and entry.owner_pid != pid:
            return False

        del self.files[filename]
        self._free(entry.start, entry.size)
        return True

    ### Helpers
    def _is_space_available(self, offset: int, size: int) -> bool:
        """Verifica se há espaço disponível para alocação."""
        end = offset + size
        for start, seg_size in self.free_segments:
            if start <= offset and end <= start + seg_size:
                return True
        return False
    
    def _occupy(self, offset: int, size: int) -> None:
        """Marca um segmento de espaço como ocupado e atualiza a lista de segmentos livres."""
        novos_segmentos: List[Tuple[int, int]] = []
        for start, seg_size in self.free_segments:
            if offset >= start + seg_size or offset + size <= start:
                # Sem sobreposição, mantém o segmento livre
                novos_segmentos.append((start, seg_size))
            else:
                before = offset - start
                after_start = offset + size
                after = (start + seg_size) - after_start
                if before > 0:
                    novos_segmentos.append((start, before))
                if after > 0:
                    novos_segmentos.append((after_start, after))
        self.free_segments = sorted(novos_segmentos, key=lambda x: x[0])  # Ordena por start

    def _free(self, offset: int, size: int) -> None:
        """Libera espaço ocupado e atualiza a lista de segmentos livres, coalescendo segmentos adjacentes."""
        self.free_segments.append((offset, size))
        self.free_segments = self._coalesce(self.free_segments)

    @staticmethod
    def _coalesce(segments: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Mescla segmentos adjacentes para evitar fragmentação."""
        segments = sorted(segments, key=lambda x: x[0])
        merged: List[Tuple[int, int]] = []
        for start, size in segments:
            if merged and merged[-1][0] + merged[-1][1] == start:
                # Adjacent segments - merge them
                merged[-1] = (merged[-1][0], merged[-1][1] + size)
            else:
                merged.append((start, size))
        return merged

    def dump(self) -> None:
        """Print current disk allocation map showing file placement."""
        disk_map: List[str] = ["0"] * self.total_blocks

        for filename, entry in self.files.items():
            disk_map[entry.start:entry.start + entry.size] = [filename] * entry.size

        map_str = " | ".join(disk_map) + " |"
        print(map_str)

    def _first_fit(self, size: int) -> Optional[int]:
        """Find first available segment that can fit the requested size.
        """
        for start, seg_size in self.free_segments:
            if seg_size >= size:
                return start
        return None