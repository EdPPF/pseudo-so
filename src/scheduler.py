"""Process scheduler implementing FIFO for real-time processes and multilevel feedback queues for user processes."""

from collections import deque
from typing import Deque, List, Optional

from .memory_manager import MemoryManager
from .process import Process, ProcessState
from .resource_manager import ResourceManager

## Constantes utilizadas pelo algoritmo de escalonamento
TIME_QUANTUM = 1        # Fatia de tempo para processos de usuário (ms)
AGING_THRESHOLD = 5     # Tempo de espera para aumentar a prioridade (aging)


class Scheduler:
    def __init__(self, mem: MemoryManager, res: ResourceManager) -> None:   #Inicializa escalonador
        self.memory = mem           # Referência ao gerenciador de memória
        self.resources = res        # Referência ao gerenciador de recursos

        ## Fila de admissão
        self.admission: Deque[Process] = deque()    # Processos que aguardam memória ou recursos
        self.rt_queue: Deque[Process] = deque()     # Fila FIFO exclusiva para processos de tempo real
        self.user_queues: List[Deque[Process]] = [  # Filas para processos de usuário (níveis 1-3)
            deque() for _ in range(3)
        ]  
        self.current: Optional[Process] = None      # Processo atualmente utilizando a CPU


    def add_new_process(self, proc: Process) -> None:   # Adiciona um processo recém-chegado à fila de admissão
        self.admission.append(proc)


    def try_admit(self) -> None:                        # Tenta admitir os processos presentes na fila de admissão: se houver memória e recursos disponíveis, o processo é colocado na fila de prontos; caso contrário, permanece aguardando
        pending = deque()                               # Nova fila contendo apenas os processos que continuarão esperando
        while self.admission:                           # Percorre todos os processos da fila de admissão
            proc = self.admission.popleft()             # Remove o primeiro processo da fila
            if self._allocate_resources(proc):          # Tenta alocar memória e recursos
                proc.state = ProcessState.READY         # Processo passa para o estado READY
                self._enqueue_ready(proc)               # Coloca o processo na fila de prontos correspondente
            else:
                # Keep waiting for resources
                pending.append(proc)                    # Não foi possível admitir, continua aguardando.

        self.admission = pending                        # Atualiza a fila de admissão.


    def _allocate_resources(self, proc: Process) -> bool:   # Tenta alocar memória e recursos para um process
        page_table = self.memory.admit_process(         # Solicita memória ao gerenciador de memória
            proc.pid, proc.is_real_time, proc.memory_blocks
        )
        if not page_table:                              # Se não houver memória suficiente, o processo não pode ser admitido
            return False
        
        if not proc.is_real_time and not self.resources.allocate(   # Tenta reservar dispositivos de E/S para processo de usuário
            proc.printers, proc.scanners, proc.modems, proc.sata
        ):
            self.memory.release_process(proc.pid)        # Desfaz a alocação de memória caso não haja recursos disponíveis
            return False
        
        proc.page_faults = page_table.process_reference_string(proc.reference_string)   # Processa a string de referência utilizando o algoritmo LRU e armazena a quantidade de faltas de página
        return True                                      # Processo admitido com sucesso


    def _enqueue_ready(self, proc: Process) -> None:    # Insere um processo na fila de prontos correspondente à sua prioridade
        if proc.is_real_time:                           # Processos de tempo real utilizam uma fila FIFO exclusiva
            self.rt_queue.append(proc)
        else:
            level = proc.current_queue_level - 1        # Converte a prioridade (1, 2 ou 3) para o índice da lista (0, 1 ou 2)
            self.user_queues[level].append(proc)


    def dispatch(self) -> Optional[Process]:            # Seleciona o próximo processo que utilizará a CPU
        if self.current and self.current.state == ProcessState.RUNNING:     # Se já existe um processo executando, ele continua utilizando a CPU
            return self.current
        # Seleciona o próximo processo
        if self.rt_queue:
            self.current = self.rt_queue.popleft()      # Remove o primeiro processo da fila FIFO
        else:
            # Procura um processo nas filas de usuário, começando pela fila de maior prioridade
            for q in self.user_queues:
                if q:
                    self.current = q.popleft()          # Se a fila não estiver vazia, remove o primeiro processo
                    break
            else:
                self.current = None                     # Nenhum processo disponível para execução
        
        if self.current:
            self.current.state = ProcessState.RUNNING   # Caso algum processo tenha sido selecionado, altera o estado para RUNNING
            self.current.waited_time = 0                # Reinicia o contador de tempo de espera (aging)
            
            if not self.current.started:                # Exibe as informações do processo apenas no primeiro despacho
                self._print_dispatch(self.current)
            print(f"process {self.current.pid} =>")     # Indica qual processo está em execução
            
            if not self.current.started:                # Imprime a mensagem STARTED apenas na primeira execução
                print(f"    P{self.current.pid} STARTED")
                self.current.started = True             # Marca que o processo já iniciou sua execução
        return self.current                             # Retorna o processo escolhido para executar


    def tick(self) -> None:                             # Simula 1 ms de execução da CPU e realiza as operações de escalonamento

        ## Tenta admitir novos processos que estavam aguardando memória ou recursos
        self.try_admit()

        ## Aplica o mecanismo de aging aos processos nas filas de usuário
        for lvl, q in enumerate(self.user_queues):
            for _ in range(len(q)):                     # Percorre todos os processos da fila atual
                proc = q.popleft()                      # Remove temporariamente o processo da fila
                proc.waited_time += 1                   # Incrementa o tempo de espera do processo
                # Se o processo esperou tempo suficiente e ainda não está na fila de maior prioridade, aumenta sua prioridade
                if proc.waited_time >= AGING_THRESHOLD and proc.current_queue_level > 1:
                    proc.current_queue_level -= 1 
                    proc.waited_time = 0                # Reinicia o contador de espera após a promoção
                self._enqueue_ready(proc)               # Reinsere o processo na fila correspondente à sua prioridade atual
        
        ## Seleciona o próximo processo para utilizar a CPU
        proc = self.dispatch()
        if proc is None:                                # Caso nenhum processo esteja disponível, a CPU permanece ociosa
            return
        
        ## Executa o processo durante um quantum de tempo
        
        if proc.is_real_time:  
            # Processos de tempo real não sofrem preempção                     
            proc.remaining_time -= 1
            proc.instructions_executed += 1
            print(f"    P{proc.pid} instruction {proc.instructions_executed}")
            finished = proc.remaining_time == 0  
        else:
            # Processos de usuário executam apenas durante um quantum
            exec_time = min(TIME_QUANTUM, proc.remaining_time)
            proc.remaining_time -= exec_time
            proc.instructions_executed += exec_time
            for i in range(exec_time):
                print(
                    f"    P{proc.pid} instruction {proc.instructions_executed - exec_time + i + 1}"
                )
            finished = proc.remaining_time == 0

        if finished:                                   
            print(f"    P{proc.pid} return SIGINT")     # Exibe a mensagem de finalização
            self._terminate_process(proc)               # Libera memória e recursos utilizados pelo processo
            self.current = None                         # Libera a CPU
        else:
            # Processos de usuário sofrem preempção ao fim do quantum
            if not proc.is_real_time:
                proc.state = ProcessState.READY         # Retorna ao estado READY
                if proc.current_queue_level < 3:        # Rebaixa a prioridade caso ainda não esteja na menor fila
                    proc.current_queue_level += 1
                self._enqueue_ready(proc)               # Insere novamente o processo na fila de prontos
                self.current = None                     # Libera a CPU para o próximo despacho


    def _terminate_process(self, proc: Process) -> None:    # Libera os recursos utilizados quando um processo termina
        """Clean up resources when process terminates."""
        proc.state = ProcessState.TERMINATED            # Atualiza o estado do processo para TERMINATED

        # Release memory frames
        self.memory.release_process(proc.pid)           # Libera os quadros de memória ocupados pelo processo
        # Release resources (user processes only)
        if not proc.is_real_time:                       # Libera os recursos de E/S utilizados
            self.resources.free(proc.printers, proc.scanners, proc.modems, proc.sata)


    @staticmethod
    def _print_dispatch(proc: Process) -> None:         # Exibe as informações do processo despachado para execução
        print("dispatcher =>")
        print(f"    PID: {proc.pid}")
        print(f"    frames: {proc.memory_blocks}")
        print(f"    priority: {proc.priority}")
        print(f"    time: {proc.cpu_time}")
        print(f"    printers: {proc.printers}")
        print(f"    scanners: {proc.scanners}")
        print(f"    modems: {proc.modems}")
        print(f"    drives: {proc.sata}")
