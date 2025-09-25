"""
Script d'analyse et sauvegarde des déficits de magasins et matériels.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.manager import MaterialManager
from src.core.exceptions import MaterialManagerError


def print_separator(title: str = "", width: int = 80) -> None:
    """Affiche un séparateur avec titre optionnel."""
    print("=" * width)
    if title:
        print(f" {title} ".center(width, "="))
        print("=" * width)


def analyze_and_save_deficits(file_path: str, output_dir: str = "output"):
    """
    Analyse complète des déficits avec sauvegarde des résultats.

    Args:
        file_path: Chemin vers le fichier de données
        output_dir: Répertoire de sortie pour les fichiers
    """
    try:
        # Créer le répertoire de sortie
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Initialiser le gestionnaire
        print_separator("ANALYSE DES DÉFICITS - MAGASINS ET MATÉRIELS")
        print(f"📁 Fichier source: {file_path}")
        print(f"💾 Répertoire de sortie: {output_path.absolute()}")

        manager = MaterialManager()
        manager.load_data(file_path)

        # Obtenir l'aperçu des données
        overview = manager.get_data_overview()
        print(f"\n📊 Données chargées:")
        print(f"   Nomenclatures: {overview['nomenclatures_count']:,}")
        print(f"   Magasins: {overview['magasins_count']:,}")
        print(f"   Exploitation (U): {overview['exploitation_entries']:,}")
        print(f"   Stock (C): {overview['stock_entries']:,}")

        # Analyse des déficits
        print_separator("ANALYSE DES DÉFICITS")
        deficits_result = manager.analyze_deficits()
        deficits_df = deficits_result.data
        summary = deficits_result.summary

        print(f"📈 Résumé global:")
        print(f"   Total déficits: {summary.get('total_deficits', 0):,}")
        print(f"   Magasins concernés: {summary.get('magasins_concernes', 0):,}")
        print(f"   Déficit total: {summary.get('deficit_total', 0):,.0f}")
        print(f"   Surplus de stock: {summary.get('surplus_stock_count', 0):,} cas ({summary.get('surplus_stock_total', 0):,.0f})")
        print(f"   Manque de stock: {summary.get('manque_stock_count', 0):,} cas ({summary.get('manque_stock_total', 0):,.0f})")

        # 1. DÉFICITS PAR MAGASIN
        print_separator("DÉFICITS PAR MAGASIN")
        magasin_summary = manager.deficit_analyzer.get_magasin_summary(deficits_result)

        print("🏢 Top 15 magasins avec les plus gros déficits:")
        top_magasins_deficits = magasin_summary.head(15)
        print(top_magasins_deficits.to_string(index=False))

        # Sauvegarder les déficits par magasin
        magasin_file = output_path / f"deficits_par_magasin_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        magasin_summary.to_csv(magasin_file, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {magasin_file}")

        # 2. MATÉRIELS LES PLUS DÉFICITAIRES
        print_separator("MATÉRIELS LES PLUS DÉFICITAIRES")

        # Top déficits par valeur absolue
        top_deficits = manager.deficit_analyzer.get_top_deficits(deficits_result, 20, by_abs_value=True)
        print("🔧 Top 20 matériels avec les plus gros déficits (valeur absolue):")
        print(top_deficits.to_string(index=False))

        # Sauvegarder les top déficits
        top_deficits_file = output_path / f"top_deficits_materiels_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        top_deficits.to_csv(top_deficits_file, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {top_deficits_file}")

        # 3. SURPLUS DE STOCK (C > U, déficit positif)
        print_separator("SURPLUS DE STOCK (STOCK > EXPLOITATION)")
        surplus_stock = deficits_df[deficits_df['deficit'] > 0].copy()
        surplus_sorted = surplus_stock.sort_values('deficit', ascending=False)

        print(f"🟡 {len(surplus_stock):,} cas de surplus de stock trouvés")
        print("Top 15 cas de surplus de stock:")
        print(surplus_sorted.head(15).to_string(index=False))

        # Sauvegarder surplus de stock
        surplus_file = output_path / f"surplus_stock_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        surplus_sorted.to_csv(surplus_file, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {surplus_file}")

        # 4. MANQUE DE STOCK (U > C, déficit négatif)
        print_separator("MANQUE DE STOCK (EXPLOITATION > STOCK)")
        manque_stock = deficits_df[deficits_df['deficit'] < 0].copy()
        manque_sorted = manque_stock.sort_values('deficit')

        print(f"🔴 {len(manque_stock):,} cas de manque de stock trouvés")
        print("Top 15 cas de manque de stock:")
        print(manque_sorted.head(15).to_string(index=False))

        # Sauvegarder manque de stock
        manque_file = output_path / f"manque_stock_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        manque_sorted.to_csv(manque_file, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {manque_file}")

        # 5. ANALYSE PAR NOMENCLATURE
        print_separator("ANALYSE PAR NOMENCLATURE")

        # Déficits agrégés par nomenclature
        nomenclature_deficits = (deficits_df.groupby('nomenclature')
                               .agg({
                                   'deficit': ['sum', 'mean', 'count'],
                                   'quantite_exploitation': 'sum',
                                   'quantite_stock': 'sum'
                               })
                               .round(2))

        # Aplatir les colonnes
        nomenclature_deficits.columns = ['deficit_total', 'deficit_moyen', 'nb_magasins',
                                       'total_exploitation', 'total_stock']
        nomenclature_deficits = nomenclature_deficits.sort_values('deficit_total', ascending=False, key=abs)

        print("🔧 Top 15 nomenclatures par déficit total (valeur absolue):")
        print(nomenclature_deficits.head(15).to_string())

        # Sauvegarder analyse par nomenclature
        nomenclature_file = output_path / f"deficits_par_nomenclature_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        nomenclature_deficits.reset_index().to_csv(nomenclature_file, index=False, encoding='utf-8')
        print(f"\n💾 Sauvegardé: {nomenclature_file}")

        # 6. TOUS LES DÉFICITS (FICHIER COMPLET)
        print_separator("SAUVEGARDE COMPLÈTE")

        # Sauvegarder tous les déficits
        all_deficits_file = output_path / f"tous_les_deficits_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        deficits_df.to_csv(all_deficits_file, index=False, encoding='utf-8')
        print(f"💾 Fichier complet sauvegardé: {all_deficits_file}")
        print(f"   Contient {len(deficits_df):,} lignes de déficits")

        # Export Excel avec plusieurs feuilles
        excel_file = output_path / f"analyse_deficits_complete_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Feuille résumé par magasin
            magasin_summary.to_excel(writer, sheet_name='Deficits_par_Magasin', index=False)

            # Feuille top déficits
            top_deficits.to_excel(writer, sheet_name='Top_Deficits_Materiels', index=False)

            # Feuille surplus de stock
            surplus_sorted.head(1000).to_excel(writer, sheet_name='Surplus_Stock', index=False)

            # Feuille manque de stock
            manque_sorted.head(1000).to_excel(writer, sheet_name='Manque_Stock', index=False)

            # Feuille par nomenclature
            nomenclature_deficits.reset_index().head(1000).to_excel(writer, sheet_name='Deficits_par_Nomenclature', index=False)

            # Feuille statistiques
            stats_df = pd.DataFrame([summary]).T
            stats_df.columns = ['Valeur']
            stats_df.to_excel(writer, sheet_name='Statistiques')

        print(f"📊 Fichier Excel complet sauvegardé: {excel_file}")

        # 7. RÉSUMÉ DES FICHIERS CRÉÉS
        print_separator("FICHIERS CRÉÉS")
        print("📁 Fichiers de sortie créés:")
        for file in output_path.glob("*"):
            if file.is_file() and datetime.now().strftime('%Y%m%d_%H%M') in file.name:
                print(f"   ✅ {file.name} ({file.stat().st_size:,} bytes)")

        print_separator("ANALYSE TERMINÉE")
        print("✅ Analyse des déficits terminée avec succès !")
        print(f"💡 Consultez le répertoire '{output_dir}' pour tous les résultats")

        return manager

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Fonction principale."""
    file_path = "./data/inventaire_court.csv"
    output_dir = "deficits_output"

    if not Path(file_path).exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return

    manager = analyze_and_save_deficits(file_path, output_dir)

    if manager:
        print(f"\n🎯 Gestionnaire disponible pour analyses supplémentaires")
        return manager


if __name__ == "__main__":
    main()