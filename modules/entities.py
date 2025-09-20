"""Entités de base pour la gestion de matériel."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SupplyClass(Enum):
    """Classe logistique OTAN."""

    CLASS_I = ("I", "Vivres et rations")
    CLASS_II = ("II", "Effets vestimentaires et équipement")
    CLASS_III = ("III", "Carburants et lubrifiants")
    CLASS_IV = ("IV", "Matériels de construction")
    CLASS_V = ("V", "Munitions")
    CLASS_VI = ("VI", "Approvisionnements à usage personnel")
    CLASS_VII = ("VII", "Matériels majeurs")
    CLASS_VIII = ("VIII", "Équipement médical et pharmaceutique")
    CLASS_IX = ("IX", "Pièces de rechange")
    CLASS_X = ("X", "Matériel non militaire")

    def code(self) -> str:
        return self.value[0]

    def description(self) -> str:
        return self.value[1]


@dataclass
class Material:
    """Représentation d'un matériel géré."""

    nsn: str
    designation: str
    supply_class: SupplyClass
    serial_number: Optional[str] = None
    condition: str = "serviceable"
    history: List[str] = field(default_factory=list)

    def add_history(self, entry: str) -> None:
        timestamp = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        self.history.append(f"{timestamp} - {entry}")


@dataclass
class Location:
    """Lieu physique ou administratif."""

    name: str
    location_code: str
    location_type: str
    capacity: Optional[int] = None

    def __hash__(self) -> int:  # autorise l'utilisation en clé de dict
        return hash((self.location_code, self.location_type))


class LocationType:
    WAREHOUSE = "entrepôt"
    REPAIR_LOCAL = "atelier local"
    REPAIR_FACTORY = "usine"
    STORE = "magasin"
    TRANSPORT = "transport"
    DISPOSAL = "élimination"


class DocumentType(Enum):
    RECEPTION = "Réception"
    TRANSPORT = "Transport"
    REPAIR = "Réparation"
    STORAGE = "Stock"
    DISPOSAL = "Élimination"


@dataclass
class LogisticDocument:
    """Document logistique associé à un flux."""

    document_type: DocumentType
    reference: str
    related_nsn: str
    origin: str
    destination: str
    issued_at: datetime
    payload: Dict[str, str]


@dataclass
class TransportMission:
    """Mission de transport pour un matériel ou un lot."""

    mission_id: str
    material_nsn: str
    quantity: int
    origin: Location
    destination: Location
    carrier: str
    status: str = "planifié"
    documents: List[LogisticDocument] = field(default_factory=list)

    def mark_in_transit(self) -> None:
        self.status = "en transit"

    def mark_completed(self) -> None:
        self.status = "livré"


@dataclass
class RepairOrder:
    """Ordre de réparation pour un matériel."""

    order_id: str
    material: Material
    facility: Location
    reported_fault: str
    corrective_action: Optional[str] = None
    status: str = "diagnostic"

    def mark_in_progress(self) -> None:
        self.status = "en cours"
        self.material.add_history(f"Réparation lancée à {self.facility.name}")

    def close(self, corrective_action: str, restored_condition: str) -> None:
        self.status = "terminée"
        self.corrective_action = corrective_action
        self.material.condition = restored_condition
        self.material.add_history(
            f"Réparation terminée à {self.facility.name} - action: {corrective_action}"
        )
