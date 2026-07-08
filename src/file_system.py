from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Dataclass é usada para simplificar a criação de classes que são principalmente usadas para armazenar dados
@dataclass 
class FileEntry:            # Representação do arquivo armazenado no disco utilizando alocação contígua
    filename: str           # Nome do arquivo
    start: int              # Bloco inicial do arquivo
    size: int               # Quantidade de blocos ocupados
    owner_pid: int          # Valor -1 indica arquivos que já existiam antes da simulação (sem dono)

    def __str__(self) -> str:    # String que representa a alocação do arquivo
        return f"{self.filename} [{self.start}:{self.start + self.size - 1}] (size: {self.size}) (owner: {self.owner_pid})"
    

class FileSystem:           # Implementa um sistema de arquivos utilizando alocação contígua e estratégia First Fit

    ## Inicializa um sistema de arquivos vazio
    def __init__(self, total_blocks: int) -> None:
        self.total_blocks = total_blocks                 # Quantidade total de blocos existentes no disco.
        self.files: Dict[str, FileEntry] = {}            # Mapeia nomes de arquivos para suas entradas
        self.free_segments: List[Tuple[int, int]] = [(0, total_blocks)]  # Lista de segmentos livres (start, size)

    ## Carrega os arquivos já existentes no sistema de arquivos
    def load_existing(self, entries: List[Tuple[str, int, int]]) -> None:   
        for name, start, size in entries:                                   # Percorre cada arquivo informado
            if name in self.files:                                          # Não permite dois arquivos com o mesmo nome
                raise RuntimeError(f"Arquivo existente duplicado: {name}")  
            if start < 0 or size <= 0 or start + size > self.total_blocks:  # Verifica se a posição informada é válida
                raise RuntimeError(f"Segmento invalido para o arquivo existente {name}")
            if not self._is_space_available(start, size):                   # Verifica se existe espaço livre naquele trecho
                raise RuntimeError(f"Espaço insuficiente para carregar o arquivo existente {name}\nEm: {start}")
            self._occupy(start, size)                                       # Remove esse trecho da lista de segmentos livres
            self.files[name] = FileEntry(name, start, size, owner_pid=-1)   # Cria o objeto FileEntry e adiciona ao sistema

    ## Cria um novo arquivo utilizando alocação contígua
    def create(self, pid: int, is_real_time: bool, filename: str, size: int) -> bool:
        if size <= 0 or filename in self.files:         # Não permite criar arquivos com tamanho inválido ou nome já existente
            return False

        start = self._first_fit(size)                   # Procura o primeiro segmento livre suficientemente grande (First Fit)
        if start is None:                               # Se nenhum segmento foi encontrado, não há espaço disponível
            return False

        self._occupy(start, size)                       # Marca os blocos como ocupados
        self.files[filename] = FileEntry(filename, start, size, owner_pid=pid)  # Registra o novo arquivo
        return True

    ## Remove um arquivo do sistema de arquivos
    def delete(self, pid: int, is_real_time: bool, filename: str) -> bool:
        entry = self.files.get(filename)                # Procura o arquivo
        if entry is None:                               # Arquivo inexistente
            return False

        if not is_real_time and entry.owner_pid != pid: # Processos de usuário somente podem apagar arquivos dos quais são proprietários
            return False                                # Processos de tempo real ignoram essa restrição

        del self.files[filename]                        # Remove o arquivo do dicionário
        self._free(entry.start, entry.size)             # Libera os blocos ocupados pelo arquivo
        return True

    ## Verifica se há espaço disponível para alocação
    def _is_space_available(self, offset: int, size: int) -> bool:
        end = offset + size                             # Calcula o último bloco ocupado
        for start, seg_size in self.free_segments:      # Percorre todos os segmentos livres
            if start <= offset and end <= start + seg_size:  # Verifica se o trecho solicitado está completamente dentro de um segmento livre
                return True
        return False
    
    ## Marca um segmento de espaço como ocupado e atualiza a lista de segmentos livres
    def _occupy(self, offset: int, size: int) -> None:
        novos_segmentos: List[Tuple[int, int]] = []     # Nova lista de segmentos livres
        for start, seg_size in self.free_segments:      # Percorre todos os segmentos livres atuais
            if offset >= start + seg_size or offset + size <= start:   # Sem sobreposição, mantém o segmento livre
                novos_segmentos.append((start, seg_size))
            else:
                before = offset - start                 # Calcula quantos blocos livres permanecem antes do arquivo
                after_start = offset + size             # Primeiro bloco após o arquivo
                after = (start + seg_size) - after_start  # Quantos blocos sobram depois
                if before > 0:                          # Se sobrou espaço antes, cria novo segmento
                    novos_segmentos.append((start, before))
                if after > 0:                            # Se sobrou espaço depois, cria outro segmento
                    novos_segmentos.append((after_start, after))
        self.free_segments = sorted(novos_segmentos, key=lambda x: x[0])  # Ordena os segmentos pelo bloco inicial

    ## Libera espaço ocupado e atualiza a lista de segmentos livres, coalescendo segmentos adjacentes
    def _free(self, offset: int, size: int) -> None:
        self.free_segments.append((offset, size))        # Adiciona o espaço liberado à lista de segmentos livres
        self.free_segments = self._coalesce(self.free_segments)  # Junta segmentos vizinhos para reduzir fragmentação

    @staticmethod # Método estático porque não utiliza self, apenas recebe uma lista e devolve outra
    ## Une segmentos livres adjacentes para evitar fragmentação
    def _coalesce(segments: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        segments = sorted(segments, key=lambda x: x[0])  # Ordena os segmentos pelo bloco inicial
        merged: List[Tuple[int, int]] = []
        for start, size in segments:
            if merged and merged[-1][0] + merged[-1][1] == start:   # Se o segmento começa exatamente onde o anterior termina, eles são adjacentes
                merged[-1] = (merged[-1][0], merged[-1][1] + size)
            else:
                merged.append((start, size))            # Caso contrário, apenas adiciona o segmento
        return merged

    ## Exibe o mapa da ocupação do disco. Cada posição representa um bloco.
    def dump(self) -> None:
        disk_map: List[str] = ["0"] * self.total_blocks

        for filename, entry in self.files.items():
            disk_map[entry.start:entry.start + entry.size] = [filename] * entry.size

        map_str = " | ".join(disk_map) + " |"
        print(map_str)

    ## Implementa o algoritmo First Fit. Percorre os segmentos livres na ordem em que aparecem e retorna o primeiro segmento capaz de armazenar o arquivo solicitado
    def _first_fit(self, size: int) -> Optional[int]:
        for start, seg_size in self.free_segments:
            if seg_size >= size:
                return start
        return None
