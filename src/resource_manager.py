"""I/O resource management for exclusive device allocation."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ResourceCounts:
    """Tracks count of available I/O resources."""

    printers: int = 0
    scanners: int = 0
    modems: int = 0
    sata: int = 0

    def as_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to tuple format.

        Returns:
            Tuple of (printers, scanners, modems, sata) counts
        """
        return self.printers, self.scanners, self.modems, self.sata


class ResourceManager:
    """Manages exclusive allocation of I/O devices.

    Tracks availability of system I/O resources and ensures exclusive access.
    Real-time processes do not require I/O resources.
    """

    # System resource limits
    TOTAL_PRINTERS = 2
    TOTAL_SCANNERS = 1
    TOTAL_MODEMS = 1
    TOTAL_SATA = 2

    def __init__(self) -> None:
        """Initialize resource manager with all devices available."""
        self.available = ResourceCounts(
            printers=self.TOTAL_PRINTERS,
            scanners=self.TOTAL_SCANNERS,
            modems=self.TOTAL_MODEMS,
            sata=self.TOTAL_SATA,
        )

    def allocate(
        self,
        printers: int,
        scanners: int,
        modems: int,
        sata: int,
    ) -> bool:
        """Attempt to allocate requested I/O devices.

        Args:
            printers: Number of printers requested
            scanners: Number of scanners requested
            modems: Number of modems requested
            sata: Number of SATA devices requested

        Returns:
            True if all requested devices were allocated, False otherwise
        """
        if min(printers, scanners, modems, sata) < 0:
            return False

        # Check if enough resources are available
        if (
            printers > self.available.printers
            or scanners > self.available.scanners
            or modems > self.available.modems
            or sata > self.available.sata
        ):
            return False
        # Allocate the resources
        self.available.printers -= printers
        self.available.scanners -= scanners
        self.available.modems -= modems
        self.available.sata -= sata
        return True

    def free(
        self,
        printers: int,
        scanners: int,
        modems: int,
        sata: int,
    ) -> None:
        """Release I/O devices back to available pool.

        Args:
            printers: Number of printers to release
            scanners: Number of scanners to release
            modems: Number of modems to release
            sata: Number of SATA devices to release
        """
        if min(printers, scanners, modems, sata) < 0:
            raise ValueError("Resource counts cannot be negative")

        self.available.printers += printers
        self.available.scanners += scanners
        self.available.modems += modems
        self.available.sata += sata

        if (
            self.available.printers > self.TOTAL_PRINTERS
            or self.available.scanners > self.TOTAL_SCANNERS
            or self.available.modems > self.TOTAL_MODEMS
            or self.available.sata > self.TOTAL_SATA
        ):
            raise RuntimeError("Resource pool exceeded total device count")

    def __str__(self) -> str:
        """String representation showing available resource counts."""
        return (
            f"PRN={self.available.printers} SCN={self.available.scanners} "
            f"MDM={self.available.modems} SATA={self.available.sata}"
        )
