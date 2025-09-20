"""Procédure inspirée de la supply chain OTAN."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .entities import SupplyClass


@dataclass
class ProcedureStep:
    code: str
    title: str
    description: str


@dataclass
class LogisticProcedure:
    """Procédure standardisée pour gérer le flux logistique."""

    name: str
    steps: List[ProcedureStep]

    def as_markdown(self) -> str:
        lines = [f"# {self.name}", ""]
        for step in self.steps:
            lines.append(f"## {step.code} – {step.title}")
            lines.append(step.description)
            lines.append("")
        return "\n".join(lines).strip()


SUPPLY_CLASS_MAPPING = {
    supply_class.code(): supply_class.description() for supply_class in SupplyClass
}


def build_nato_inspired_procedure() -> LogisticProcedure:
    """Construit une procédure en 10 étapes codifiées."""

    steps = [
        ProcedureStep(
            code="SC-01",
            title="Codification du besoin (NSN)",
            description=(
                "Identifier la classe OTAN de l'article et vérifier le NSN en s'appuyant "
                "sur les classes d'approvisionnement : "
                + ", ".join(f"Classe {code} : {desc}" for code, desc in SUPPLY_CLASS_MAPPING.items())
            ),
        ),
        ProcedureStep(
            code="SC-02",
            title="Réception et inspection",
            description=(
                "Enregistrer la livraison, contrôler l'intégrité, établir la fiche de "
                "réception (document type RECEPTION) et mettre à jour le stock d'entrepôt."
            ),
        ),
        ProcedureStep(
            code="SC-03",
            title="Mise en stockage initial",
            description=(
                "Affecter un emplacement dans l'entrepôt, appliquer les règles FIFO/FEFO, "
                "et consigner la traçabilité dans l'historique du matériel."
            ),
        ),
        ProcedureStep(
            code="SC-04",
            title="Planification du transport (Mouvement code MVT)",
            description=(
                "Éditer l'ordre de transport en précisant priorité OTAN (Urgent, Routier, "
                "Aérien) et le transporteur. Créer le document TRANSPORT associé."
            ),
        ),
        ProcedureStep(
            code="SC-05",
            title="Transit et suivi",
            description=(
                "Suivre la mission de transport via son identifiant. Mettre à jour le statut "
                "en transit et consigner les événements (départ, arrivée, incidents)."
            ),
        ),
        ProcedureStep(
            code="SC-06",
            title="Réparation locale",
            description=(
                "Si l'article est réparable localement, ouvrir un ordre de réparation "
                "(code REP-L) avec diagnostic, actions correctives et retour en stock."
            ),
        ),
        ProcedureStep(
            code="SC-07",
            title="Réparation usine",
            description=(
                "Pour les réparations lourdes, réacheminer vers l'usine (code REP-F). "
                "Suivre le retour avec les documents TRANSPORT et REPAIR."
            ),
        ),
        ProcedureStep(
            code="SC-08",
            title="Distribution magasin",
            description=(
                "Transférer vers les magasins utilisateurs avec un ordre de distribution "
                "(code DIST) et décrémenter le stock magasin lors de la délivrance."
            ),
        ),
        ProcedureStep(
            code="SC-09",
            title="Gestion documentaire",
            description=(
                "Archiver tous les documents (réception, transport, réparation, stock, "
                "élimination) avec leur référence pour assurer la traçabilité OTAN."
            ),
        ),
        ProcedureStep(
            code="SC-10",
            title="Élimination et rétro-information",
            description=(
                "Programmer l'élimination (code DISPO) avec justification, notifier la chaîne "
                "logistique et remonter les informations pour mise à jour du référentiel."
            ),
        ),
    ]
    return LogisticProcedure(name="Procédure logistique OTAN simplifiée", steps=steps)
