from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ManufacturerDocumentation:
    manufacturer: str = ""
    product: str = ""
    reference: str = ""
    note: str = ""
