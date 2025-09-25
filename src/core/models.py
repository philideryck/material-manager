"""
Modèles de données pour le gestionnaire de matériel.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class InventoryItem:
    """Représente un élément d'inventaire."""
    nomenclature: str
    magasin: str
    type_donnee: str  # 'U' pour exploitation, 'C' pour stock
    quantite: float

    @property
    def is_exploitation(self) -> bool:
        """Vérifie si c'est une donnée d'exploitation."""
        return self.type_donnee == 'U'

    @property
    def is_stock(self) -> bool:
        """Vérifie si c'est une donnée de stock."""
        return self.type_donnee == 'C'


@dataclass
class DeficitItem:
    """Représente un déficit entre exploitation et stock."""
    magasin: str
    nomenclature: str
    quantite_exploitation: float
    quantite_stock: float

    @property
    def deficit(self) -> float:
        """Calcule le déficit (Stock - Exploitation)."""
        return self.quantite_stock - self.quantite_exploitation

    @property
    def has_deficit(self) -> bool:
        """Vérifie s'il y a un déficit."""
        return self.deficit != 0

    @property
    def is_surplus_stock(self) -> bool:
        """Vérifie s'il y a un surplus de stock (déficit positif)."""
        return self.deficit > 0

    @property
    def is_manque_stock(self) -> bool:
        """Vérifie s'il y a un manque de stock (déficit négatif)."""
        return self.deficit < 0


@dataclass
class AnalysisResult:
    """Résultat d'une analyse."""
    data: pd.DataFrame
    summary: Dict[str, float]
    metadata: Dict[str, any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InventoryStats:
    """Statistiques d'inventaire."""
    nombre_nomenclatures: int
    nombre_magasins: int
    nombre_total_entrees: int
    quantite_totale: float
    quantite_moyenne: float
    quantite_mediane: float
    quantite_max: float
    quantite_min: float