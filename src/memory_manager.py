from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
    

@dataclass
# Representa a tabela de páginas de um único processo e contador de faltas de página
# Cada processo possui sua própria tabela e executa o algoritmo LRU de forma independente (LRU local)
class ProcessPageTable:
    pid: int
    max_frames: int
    is_real_time: bool
    resident: OrderedDict = field(default_factory=OrderedDict) # page -> None, início = LRU
    page_faults: int = 0

    ## Processa uma string de referência e retorna o número de faltas de página (LRU local)
    def process_reference_string(self, ref_string: List[int]) -> int:
        if not ref_string:          # Se a string estiver vazia, não há páginas para acessar
            return 0
        
        # Pré-carga da primeira página
        first_page = ref_string[0]
        self.resident[first_page] = None

        # Processa o restante da string
        for page in ref_string[1:]: 
            if page in self.resident:              # Verifica se a página já está carregada
                self.resident.move_to_end(page)    # Vira a mais recente usada
            else:
                self.page_faults += 1              # Página não encontrada na memória, ocorreu uma falta de página
                if len(self.resident) >= self.max_frames:   # Verifica se todos os frames já estão ocupados
                    self.resident.popitem(last=False)       # Remove a página menos recentemente utilizada, que sempre fica no início do OrderedDict
                self.resident[page] = None          # Carrega a nova página na memória.b Ela passa automaticamente a ser a mais recente         
        return self.page_faults                     # Retorna o número de faltas de página


## Gerencia a alocação de memória para processos de tempo real e de usuário
# A implementação utiliza contadores de frames livres em vez de representar cada frame individualmente
class MemoryManager:
    TOTAL_BLOCKS = 20                               # Quantidade total de frames existentes na memória
    RT_RESERVED = 8                                 # Frames reservados para processos de tempo real
    USER_RESERVED = 12                              # Frames reservados para processos de usuário
    USER_START = RT_RESERVED                        # Primeiro frame pertencente à área de usuário
    USER_BLOCKS = TOTAL_BLOCKS - RT_RESERVED        # Quantidade total de frames da área de usuário

    ## Inicializa o gerenciador de memória
    def __init__(self) -> None:
        self.rt_frames_free = self.RT_RESERVED      # Inicialmente todos os frames da área de tempo real estão livres
        self.user_frames_free = self.USER_RESERVED  # Inicialmente todos os frames da área de usuário também estão livres
        self.page_tables: Dict[int, ProcessPageTable] = {}   # Dicionário contendo a tabela de páginas de cada processo admitido

    ## Tenta admitir um processo na memória
    ## Caso existam frames suficientes, reserva a quantidade solicitada e cria sua tabela de páginas
    def admit_process(
            self, pid: int, is_real_time: bool,
            max_frames: int, first_page: Optional[int] = None
    ) -> Optional[ProcessPageTable]:
        
        if max_frames <= 0:                         # Não faz sentido admitir um processo que solicite zero ou menos frames
            return None

        if is_real_time:                            # Se for processo de tempo real
            if max_frames > self.rt_frames_free:    # verifica se existem frames suficientes
                return None
            self.rt_frames_free -= max_frames       # Reserva os frames para esse processo
        else:
            if max_frames > self.user_frames_free:  # Verifica disponibilidade para processo de usuário
                return None
            self.user_frames_free -= max_frames     # Reserva os frames

        # Cria a tabela de páginas do processo
        page_table = ProcessPageTable(pid=pid, max_frames=max_frames, is_real_time=is_real_time)
        self.page_tables[pid] = page_table          # Registra essa tabela utilizando o PID como chave do dicionário
        return page_table                           # Retorna a tabela criada
    
    ## Libera toda a memória ocupada por um processo quando sua execução termina
    def release_process(self, pid: int) -> None:
        table = self.page_tables.pop(pid, None)
        if table:                                   # Se o processo realmente existia
            if table.is_real_time:                  # Devolve os frames à região correta
                self.rt_frames_free += table.max_frames
            else:
                self.user_frames_free += table.max_frames
