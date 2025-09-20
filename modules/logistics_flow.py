"""Gestion complète du flux logistique du matériel."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from .entities import (
    DocumentType,
    Location,
    LocationType,
    LogisticDocument,
    Material,
    RepairOrder,
    SupplyClass,
    TransportMission,
)


class InventoryManager:
    """Coordonne le cycle de vie du matériel."""

    def __init__(self) -> None:
        self.materials: Dict[str, Material] = {}
        self.locations: Dict[str, Location] = {}
        self.stock: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.transport_missions: Dict[str, TransportMission] = {}
        self.repair_orders: Dict[str, RepairOrder] = {}
        self.documents: List[LogisticDocument] = []

    # --- Gestion des référentiels ---
    def register_location(self, location: Location) -> None:
        self.locations[location.location_code] = location

    def register_material(self, material: Material) -> None:
        self.materials[material.nsn] = material
        material.add_history("Enregistré dans le système")

    # --- Réception ---
    def receive_material(
        self,
        nsn: str,
        quantity: int,
        warehouse_code: str,
        reception_ref: str,
        inspector: str,
    ) -> LogisticDocument:
        material = self.materials[nsn]
        warehouse = self.locations[warehouse_code]
        self.stock[warehouse_code][nsn] += quantity
        material.add_history(
            f"Réception de {quantity} unités à {warehouse.name} (réf {reception_ref})"
        )
        document = LogisticDocument(
            document_type=DocumentType.RECEPTION,
            reference=reception_ref,
            related_nsn=nsn,
            origin="Fournisseur",
            destination=warehouse.name,
            issued_at=datetime.utcnow(),
            payload={
                "inspecteur": inspector,
                "quantité": str(quantity),
                "entrepôt": warehouse.name,
            },
        )
        self.documents.append(document)
        return document

    # --- Transport ---
    def plan_transport(
        self,
        mission_id: str,
        nsn: str,
        quantity: int,
        origin_code: str,
        destination_code: str,
        carrier: str,
        document_ref: str,
        movement_priority: str,
    ) -> TransportMission:
        origin = self.locations[origin_code]
        destination = self.locations[destination_code]
        if self.stock[origin_code][nsn] < quantity:
            raise ValueError("Stock insuffisant pour planifier ce transport")
        mission = TransportMission(
            mission_id=mission_id,
            material_nsn=nsn,
            quantity=quantity,
            origin=origin,
            destination=destination,
            carrier=carrier,
        )
        document = LogisticDocument(
            document_type=DocumentType.TRANSPORT,
            reference=document_ref,
            related_nsn=nsn,
            origin=origin.name,
            destination=destination.name,
            issued_at=datetime.utcnow(),
            payload={
                "priorité": movement_priority,
                "transporteur": carrier,
                "quantité": str(quantity),
            },
        )
        mission.documents.append(document)
        self.transport_missions[mission_id] = mission
        self.documents.append(document)
        mission.mark_in_transit()
        self.stock[origin_code][nsn] -= quantity
        self.materials[nsn].add_history(
            f"Transport mission {mission_id} lancé vers {destination.name}"
        )
        return mission

    def complete_transport(self, mission_id: str, document_ref: str) -> LogisticDocument:
        mission = self.transport_missions[mission_id]
        mission.mark_completed()
        destination_code = mission.destination.location_code
        self.stock[destination_code][mission.material_nsn] += mission.quantity
        document = LogisticDocument(
            document_type=DocumentType.TRANSPORT,
            reference=document_ref,
            related_nsn=mission.material_nsn,
            origin=mission.origin.name,
            destination=mission.destination.name,
            issued_at=datetime.utcnow(),
            payload={
                "statut": mission.status,
                "quantité": str(mission.quantity),
            },
        )
        self.documents.append(document)
        self.materials[mission.material_nsn].add_history(
            f"Transport mission {mission.mission_id} livrée à {mission.destination.name}"
        )
        return document

    # --- Réparation ---
    def create_repair_order(
        self,
        order_id: str,
        nsn: str,
        facility_code: str,
        fault_description: str,
        send_to_factory: bool = False,
    ) -> RepairOrder:
        material = self.materials[nsn]
        facility = self.locations[facility_code]
        if send_to_factory and facility.location_type != LocationType.REPAIR_FACTORY:
            raise ValueError("La destination doit être une usine pour un envoi usine")
        order = RepairOrder(
            order_id=order_id,
            material=material,
            facility=facility,
            reported_fault=fault_description,
        )
        self.repair_orders[order_id] = order
        order.mark_in_progress()
        material.condition = "non opérationnel"
        material.add_history(f"Ordre de réparation {order_id} créé pour {fault_description}")
        return order

    def close_repair_order(
        self,
        order_id: str,
        corrective_action: str,
        restored_condition: str,
        document_ref: str,
    ) -> LogisticDocument:
        order = self.repair_orders[order_id]
        order.close(corrective_action, restored_condition)
        document = LogisticDocument(
            document_type=DocumentType.REPAIR,
            reference=document_ref,
            related_nsn=order.material.nsn,
            origin=order.facility.name,
            destination="Retour stock",
            issued_at=datetime.utcnow(),
            payload={
                "ordre": order_id,
                "action": corrective_action,
                "condition": restored_condition,
            },
        )
        self.documents.append(document)
        return document

    # --- Stock magasin ---
    def assign_to_store(
        self, nsn: str, store_code: str, quantity: int, document_ref: str
    ) -> LogisticDocument:
        if self.stock[store_code][nsn] < quantity:
            raise ValueError("Stock insuffisant pour affecter au magasin")
        document = LogisticDocument(
            document_type=DocumentType.STORAGE,
            reference=document_ref,
            related_nsn=nsn,
            origin=self.locations[store_code].name,
            destination=f"Distribution finale ({store_code})",
            issued_at=datetime.utcnow(),
            payload={"quantité": str(quantity)},
        )
        self.stock[store_code][nsn] -= quantity
        self.documents.append(document)
        self.materials[nsn].add_history(
            f"{quantity} unités affectées à la distribution magasin {store_code}"
        )
        return document

    # --- Élimination ---
    def schedule_disposal(
        self, nsn: str, disposal_code: str, quantity: int, reason: str, document_ref: str
    ) -> LogisticDocument:
        if self.stock[disposal_code][nsn] < quantity:
            raise ValueError("Stock insuffisant pour élimination")
        document = LogisticDocument(
            document_type=DocumentType.DISPOSAL,
            reference=document_ref,
            related_nsn=nsn,
            origin=self.locations[disposal_code].name,
            destination="Centre d'élimination",
            issued_at=datetime.utcnow(),
            payload={"motif": reason, "quantité": str(quantity)},
        )
        self.stock[disposal_code][nsn] -= quantity
        self.documents.append(document)
        self.materials[nsn].add_history(
            f"{quantity} unités envoyées à l'élimination pour {reason}"
        )
        return document

    # --- Accès aux données ---
    def get_stock_snapshot(self) -> Dict[str, Dict[str, int]]:
        return {loc: dict(stock) for loc, stock in self.stock.items()}

    def get_documents_by_type(self, document_type: DocumentType) -> List[LogisticDocument]:
        return [doc for doc in self.documents if doc.document_type == document_type]

    def describe_material(self, nsn: str) -> Dict[str, object]:
        material = self.materials[nsn]
        return {
            "NSN": material.nsn,
            "Désignation": material.designation,
            "Classe": f"{material.supply_class.code()} - {material.supply_class.description()}",
            "Condition": material.condition,
            "Historique": material.history,
        }


def build_default_manager() -> InventoryManager:
    """Construit un gestionnaire avec des données exemples."""

    manager = InventoryManager()
    # Enregistrer des lieux
    manager.register_location(
        Location("Entrepôt Ouest", "WH-01", LocationType.WAREHOUSE, capacity=1000)
    )
    manager.register_location(
        Location("Atelier Régional", "REP-LOC-1", LocationType.REPAIR_LOCAL, capacity=50)
    )
    manager.register_location(
        Location("Usine Centrale", "REP-FACT-1", LocationType.REPAIR_FACTORY, capacity=200)
    )
    manager.register_location(
        Location("Magasin Nord", "STORE-01", LocationType.STORE, capacity=200)
    )
    manager.register_location(
        Location("Zone Déchets", "DISP-01", LocationType.DISPOSAL, capacity=500)
    )

    # Enregistrer un matériel
    generator = Material(
        nsn="6115-01-274-7387",
        designation="Groupe électrogène 10kW",
        supply_class=SupplyClass.CLASS_VII,
        serial_number="GEN-0001",
    )
    manager.register_material(generator)

    # Initialiser un stock de départ
    manager.stock["WH-01"][generator.nsn] = 10

    return manager
