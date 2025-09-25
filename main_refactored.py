"""
Interface simplifiée pour l'analyse des matériels - Version refactorisée.
"""
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.manager import MaterialManager
from src.core.exceptions import MaterialManagerError


def print_separator(title: str = "") -> None:
    """Affiche un séparateur avec titre optionnel."""
    print("=" * 60)
    if title:
        print(f" {title} ".center(60, "="))
        print("=" * 60)


def print_stats(stats) -> None:
    """Affiche les statistiques de manière formatée."""
    print(f"📊 Nomenclatures: {stats.nombre_nomenclatures:,}")
    print(f"🏢 Magasins: {stats.nombre_magasins:,}")
    print(f"📝 Entrées totales: {stats.nombre_total_entrees:,}")
    print(f"📦 Quantité totale: {stats.quantite_totale:,.0f}")
    print(f"📈 Quantité moyenne: {stats.quantite_moyenne:.2f}")
    print(f"📊 Quantité médiane: {stats.quantite_mediane:.0f}")
    print(f"⬆️  Quantité max: {stats.quantite_max:.0f}")
    print(f"⬇️  Quantité min: {stats.quantite_min:.0f}")


def print_analysis_result(result, title: str) -> None:
    """Affiche un résultat d'analyse."""
    print_separator(title)

    if result.data.empty:
        print("Aucune donnée à afficher.")
        return

    print(result.data.to_string(index=False))

    if result.summary:
        print(f"\n📋 Résumé:")
        for key, value in result.summary.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value:,}")


def print_deficit_summary(result) -> None:
    """Affiche un résumé des déficits."""
    summary = result.summary

    print(f"\n📊 RÉSUMÉ DES DÉFICITS")
    print(f"   Total déficits détectés: {summary.get('total_deficits', 0):,}")
    print(f"   Magasins concernés: {summary.get('magasins_concernes', 0):,}")
    print(f"   Déficit total: {summary.get('deficit_total', 0):.0f}")
    print(f"   Déficit moyen: {summary.get('deficit_moyen', 0):.2f}")

    if 'surexploitation_count' in summary:
        print(f"\n🔴 Surexploitation:")
        print(f"   Cas: {summary['surexploitation_count']:,}")
        print(f"   Total: {summary.get('surexploitation_total', 0):.0f}")

    if 'sous_exploitation_count' in summary:
        print(f"\n🟡 Sous-exploitation:")
        print(f"   Cas: {summary['sous_exploitation_count']:,}")
        print(f"   Total: {summary.get('sous_exploitation_total', 0):.0f}")


def demonstrate_analysis(file_path: str) -> None:
    """
    Démonstration complète de l'analyse.

    Args:
        file_path: Chemin vers le fichier de données
    """
    try:
        # Initialiser le gestionnaire
        print_separator("INITIALISATION")
        print("🚀 Initialisation du MaterialManager...")
        manager = MaterialManager()

        # Informations sur le fichier
        print("\n📁 Informations sur le fichier:")
        file_info = manager.get_file_info(file_path)
        if 'error' in file_info:
            print(f"❌ Erreur: {file_info['error']}")
            return

        print(f"   Chemin: {file_info['path']}")
        print(f"   Existe: {file_info['exists']}")
        print(f"   Taille: {file_info.get('size_bytes', 0):,} bytes")
        print(f"   Colonnes estimées: {file_info.get('estimated_columns', 0)}")
        print(f"   Colonnes magasins: {file_info.get('estimated_magasin_columns', 0)}")

        # Chargement des données
        print_separator("CHARGEMENT DES DONNÉES")
        print("📥 Chargement et transformation des données...")
        manager.load_data(file_path)

        # Aperçu des données
        overview = manager.get_data_overview()
        print(f"\n📋 Aperçu:")
        print(f"   Format brut: {overview['raw_shape']}")
        print(f"   Format transformé: {overview['transformed_shape']}")
        print(f"   Nomenclatures: {overview['nomenclatures_count']:,}")
        print(f"   Magasins: {overview['magasins_count']:,}")
        print(f"   Quantité totale: {overview['total_quantity']:,.0f}")
        print(f"   Entrées exploitation (U): {overview['exploitation_entries']:,}")
        print(f"   Entrées stock (C): {overview['stock_entries']:,}")

        # Statistiques globales
        print_separator("STATISTIQUES GLOBALES")
        stats = manager.calculate_global_statistics()
        print_stats(stats)

        # Top magasins
        top_magasins = manager.get_top_magasins(10)
        print_analysis_result(top_magasins, "TOP 10 MAGASINS")

        # Top nomenclatures
        top_nomenclatures = manager.get_top_nomenclatures(10)
        print_analysis_result(top_nomenclatures, "TOP 10 NOMENCLATURES")

        # Analyse des déficits
        print_separator("ANALYSE DES DÉFICITS")
        deficits = manager.analyze_deficits()

        if not deficits.data.empty:
            print_deficit_summary(deficits)

            # Afficher les 10 plus gros déficits
            top_deficits = manager.deficit_analyzer.get_top_deficits(deficits, 10)
            print(f"\n🔍 TOP 10 DÉFICITS (par valeur absolue):")
            print(top_deficits.to_string(index=False))

            # Résumé par magasin
            magasin_summary = manager.deficit_analyzer.get_magasin_summary(deficits)
            print(f"\n🏢 RÉSUMÉ PAR MAGASIN:")
            print(magasin_summary.head(10).to_string(index=False))
        else:
            print("✅ Aucun déficit détecté !")

        # Comparaison exploitation vs stock
        comparison = manager.compare_exploitation_vs_stock()
        if not comparison.data.empty:
            print_separator("COMPARAISON EXPLOITATION vs STOCK")
            comp_summary = comparison.summary
            print(f"📊 Résumé global:")
            print(f"   Total exploitation: {comp_summary.get('total_exploitation', 0):,.0f}")
            print(f"   Total stock: {comp_summary.get('total_stock', 0):,.0f}")
            print(f"   Ratio global: {comp_summary.get('ratio_global', 0):.3f}")
            print(f"   Magasins en surexploitation: {comp_summary.get('magasins_surexploitation', 0)}")
            print(f"   Magasins en sous-exploitation: {comp_summary.get('magasins_sous_exploitation', 0)}")
            print(f"   Magasins équilibrés: {comp_summary.get('magasins_equilibres', 0)}")

        # Fonctionnalités disponibles
        print_separator("FONCTIONNALITÉS DISPONIBLES")
        print("📈 Visualisations:")
        print("   manager.generate_visualizations('output/')")
        print("\n💾 Exports:")
        print("   manager.export_data('deficits.csv', 'deficits')")
        print("   manager.export_data('data.xlsx', 'transformed', 'excel')")
        print("\n🔍 Filtrage:")
        print("   manager.filter_by_magasin('NOM_MAGASIN')")
        print("   manager.filter_by_nomenclature('CODE_NOMENCLATURE')")
        print("\n📋 Listes disponibles:")
        print(f"   Magasins: {len(manager.get_available_magasins())} disponibles")
        print(f"   Nomenclatures: {len(manager.get_available_nomenclatures())} disponibles")

        print_separator("ANALYSE TERMINÉE")
        print("✅ Analyse complète réussie !")
        print("💡 Utilisez manager.<méthode>() pour accéder aux fonctionnalités")

        return manager

    except MaterialManagerError as e:
        print(f"❌ Erreur Material Manager: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None


def main() -> None:
    """Fonction principale."""
    print_separator("MATERIAL MANAGER - VERSION REFACTORISÉE")
    print("🔧 Analyseur d'inventaire avec gestion des déficits U/C")

    # Chemin par défaut
    default_file = "./data/inventaire_court.csv"

    # Vérifier si le fichier existe
    if not Path(default_file).exists():
        print(f"❌ Fichier non trouvé: {default_file}")
        print("💡 Assurez-vous que le fichier existe ou modifiez le chemin dans main_refactored.py")
        return

    # Lancer l'analyse
    manager = demonstrate_analysis(default_file)

    if manager:
        print(f"\n🎯 L'objet 'manager' est maintenant disponible pour utilisation interactive")
        # Retourner le manager pour utilisation interactive si lancé depuis un notebook
        return manager


if __name__ == "__main__":
    main()