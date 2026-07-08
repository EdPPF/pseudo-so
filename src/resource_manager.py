from dataclasses import dataclass
from typing import Tuple


@dataclass
## Representa a quantidade de dispositivos de E/S disponíveis
class ResourceCounts:
    printers: int = 0                               # Quantidade de impressoras disponíveis
    scanners: int = 0                               # Quantidade de scanners disponíveis
    modems: int = 0                                 # Quantidade de modems disponíveis
    sata: int = 0                                   # Quantidade de dispositivos SATA disponíveis

    ## Retorna todos os contadores em formato de tupla
    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.printers, self.scanners, self.modems, self.sata

## Classe responsável pelo gerenciamento dos recursos de E/S
class ResourceManager:
    # Quantidade total de dispositivos existentes no sistema
    TOTAL_PRINTERS = 2 
    TOTAL_SCANNERS = 1
    TOTAL_MODEMS = 1
    TOTAL_SATA = 2

    ## Inicializa o gerenciador de recursos com todos os recursos disnponíveis
    def __init__(self) -> None:
        self.available = ResourceCounts(
            printers=self.TOTAL_PRINTERS,
            scanners=self.TOTAL_SCANNERS,
            modems=self.TOTAL_MODEMS,
            sata=self.TOTAL_SATA,
        )

    ## Tenta alocar os dispositivos solicitados por um processo
    def allocate(
        self,
        printers: int,
        scanners: int,
        modems: int,
        sata: int,
    ) -> bool:

        # Verifica se algum valor solicitado é negativo
        if min(printers, scanners, modems, sata) < 0:
            return False

        # Verifica se existem recursos suficientes
        if (
            printers > self.available.printers
            or scanners > self.available.scanners
            or modems > self.available.modems
            or sata > self.available.sata
        ):
            return False
        
        # Com todos os recursos disponíveis, reserva cada dispositivo solicitado
        self.available.printers -= printers
        self.available.scanners -= scanners
        self.available.modems -= modems
        self.available.sata -= sata
        return True                                 # Indica que a alocação foi realizada

    ## Libera os recursos utilizados por um processo
    def free(
        self,
        printers: int,
        scanners: int,
        modems: int,
        sata: int,
    ) -> None:

        if min(printers, scanners, modems, sata) < 0:   # Não é permitido liberar uma quantidade negativa de dispositivos
            raise ValueError("Resource counts cannot be negative")

        # Devolve cada recurso ao sistema
        self.available.printers += printers
        self.available.scanners += scanners
        self.available.modems += modems
        self.available.sata += sata

        # Verifica se algum contador ultrapassou a quantidade total existente no sistema
        if (
            self.available.printers > self.TOTAL_PRINTERS
            or self.available.scanners > self.TOTAL_SCANNERS
            or self.available.modems > self.TOTAL_MODEMS
            or self.available.sata > self.TOTAL_SATA
        ):
            raise RuntimeError("Resource pool exceeded total device count")

    ## Define como o objeto será exibido ao utilizar print()
    def __str__(self) -> str:
        return (
            f"PRN={self.available.printers} SCN={self.available.scanners} "
            f"MDM={self.available.modems} SATA={self.available.sata}"
        )
