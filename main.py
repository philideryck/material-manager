"""Application CLI de gestion de matériel."""

from typing import Callable, Dict

from modules.entities import DocumentType
from modules.logistics_flow import InventoryManager, build_default_manager
from modules.procedure import build_nato_inspired_procedure


def afficher_menu() -> None:
    print("\n=== Gestion de Matériel ===")
    print("1. Consulter un matériel")
    print("2. Réceptionner du matériel")
    print("3. Planifier un transport")
    print("4. Clore un transport")
    print("5. Créer un ordre de réparation")
    print("6. Clore un ordre de réparation")
    print("7. Consulter le stock")
    print("8. Afficher la procédure OTAN")
    print("9. Lister les documents")
    print("0. Quitter")


def choisir_document_type() -> DocumentType:
    mapping = {str(index): doc for index, doc in enumerate(DocumentType, start=1)}
    for key, doc in mapping.items():
        print(f"{key}. {doc.value}")
    choix = input("Type de document : ")
    return mapping[choix]


def consulter_materiel(manager: InventoryManager) -> None:
    nsn = input("NSN du matériel : ")
    details = manager.describe_material(nsn)
    print("--- Informations ---")
    for key, value in details.items():
        if key == "Historique":
            print("Historique :")
            for entry in value:
                print(f"  - {entry}")
        else:
            print(f"{key} : {value}")


def receptionner(manager: InventoryManager) -> None:
    nsn = input("NSN : ")
    quantite = int(input("Quantité reçue : "))
    entrepot = input("Code entrepôt : ")
    reference = input("Référence de réception : ")
    inspecteur = input("Inspecteur : ")
    document = manager.receive_material(nsn, quantite, entrepot, reference, inspecteur)
    print(f"Réception enregistrée ({document.reference}).")


def planifier_transport(manager: InventoryManager) -> None:
    mission_id = input("Identifiant mission : ")
    nsn = input("NSN : ")
    quantite = int(input("Quantité à transporter : "))
    origine = input("Code origine : ")
    destination = input("Code destination : ")
    transporteur = input("Transporteur : ")
    reference = input("Référence document : ")
    priorite = input("Priorité OTAN (Urgent/Routier/Aérien) : ")
    mission = manager.plan_transport(
        mission_id, nsn, quantite, origine, destination, transporteur, reference, priorite
    )
    print(f"Mission {mission.mission_id} planifiée et en transit.")


def clore_transport(manager: InventoryManager) -> None:
    mission_id = input("Identifiant mission : ")
    reference = input("Référence document clôture : ")
    document = manager.complete_transport(mission_id, reference)
    print(f"Transport {mission_id} clôturé ({document.reference}).")


def creer_reparation(manager: InventoryManager) -> None:
    ordre = input("Identifiant ordre : ")
    nsn = input("NSN : ")
    atelier = input("Code atelier/usine : ")
    panne = input("Description panne : ")
    en_usine = input("Envoyer en usine ? (o/n) : ").lower() == "o"
    manager.create_repair_order(ordre, nsn, atelier, panne, send_to_factory=en_usine)
    print(f"Ordre {ordre} créé.")


def clore_reparation(manager: InventoryManager) -> None:
    ordre = input("Identifiant ordre : ")
    action = input("Action corrective : ")
    condition = input("Condition restaurée : ")
    reference = input("Référence document : ")
    manager.close_repair_order(ordre, action, condition, reference)
    print(f"Ordre {ordre} clôturé.")


def consulter_stock(manager: InventoryManager) -> None:
    print("--- Stock ---")
    for location_code, contents in manager.get_stock_snapshot().items():
        print(f"{location_code} :")
        if contents:
            for nsn, quantity in contents.items():
                print(f"  - {nsn} : {quantity}")
        else:
            print("  (vide)")


def afficher_procedure() -> None:
    procedure = build_nato_inspired_procedure()
    print(procedure.as_markdown())


def lister_documents(manager: InventoryManager) -> None:
    doc_type = choisir_document_type()
    documents = manager.get_documents_by_type(doc_type)
    if not documents:
        print("Aucun document trouvé.")
        return
    for document in documents:
        print(f"- Réf {document.reference} | {document.origin} -> {document.destination}")
        for key, value in document.payload.items():
            print(f"    {key} : {value}")


def main() -> None:
    manager = build_default_manager()
    actions: Dict[str, Callable[[InventoryManager], None]] = {
        "1": consulter_materiel,
        "2": receptionner,
        "3": planifier_transport,
        "4": clore_transport,
        "5": creer_reparation,
        "6": clore_reparation,
        "7": consulter_stock,
        "8": lambda _: afficher_procedure(),
        "9": lister_documents,
    }

    while True:
        afficher_menu()
        choix = input("Votre choix : ")
        if choix == "0":
            print("Au revoir !")
            break
        action = actions.get(choix)
        if not action:
            print("Choix invalide")
            continue
        try:
            action(manager)
        except Exception as exc:  # pour la démo CLI
            print(f"Erreur : {exc}")


if __name__ == "__main__":
    main()
