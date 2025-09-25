"""
Affichage visuel du résumé des déficits magasins et matériels.
"""
import sys
from pathlib import Path
import pandas as pd

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.manager import MaterialManager


def display_deficits_summary():
    """Affiche un résumé visuel des déficits."""

    print("╔" + "="*78 + "╗")
    print("║" + " RÉSUMÉ DES DÉFICITS - MAGASINS ET MATÉRIELS ".center(78) + "║")
    print("╚" + "="*78 + "╝")

    try:
        # Charger les données
        manager = MaterialManager()
        manager.load_data('./data/inventaire_court.csv')

        # Analyser les déficits
        deficits_result = manager.analyze_deficits()
        summary = deficits_result.summary

        print("\n📊 STATISTIQUES GLOBALES")
        print("─" * 50)
        print(f"🏢 Magasins analysés          : {manager.get_data_overview()['magasins_count']:>8,}")
        print(f"🔧 Nomenclatures analysées    : {manager.get_data_overview()['nomenclatures_count']:>8,}")
        print(f"📈 Total déficits détectés    : {summary.get('total_deficits', 0):>8,}")
        print(f"🎯 Magasins concernés         : {summary.get('magasins_concernes', 0):>8,}")
        print(f"📊 Déficit total              : {summary.get('deficit_total', 0):>8,.0f}")

        print(f"\n🟡 SURPLUS DE STOCK (Stock > Exploitation)")
        print("─" * 50)
        print(f"   Cas détectés               : {summary.get('surplus_stock_count', 0):>8,}")
        print(f"   Quantité totale            : {summary.get('surplus_stock_total', 0):>8,.0f}")

        print(f"\n🔴 MANQUE DE STOCK (Exploitation > Stock)")
        print("─" * 50)
        print(f"   Cas détectés               : {summary.get('manque_stock_count', 0):>8,}")
        print(f"   Quantité totale            : {summary.get('manque_stock_total', 0):>8,.0f}")

        # Top magasins déficitaires
        print(f"\n🏢 TOP 10 MAGASINS DÉFICITAIRES")
        print("─" * 50)
        magasin_summary = manager.deficit_analyzer.get_magasin_summary(deficits_result)

        print("│ Rang │ Magasin │  Déficit  │ Items │ Ratio E/S │")
        print("├──────┼─────────┼───────────┼───────┼───────────┤")
        for i, (_, row) in enumerate(magasin_summary.head(10).iterrows(), 1):
            ratio = row['ratio_exp_stock']
            if ratio > 1000:
                ratio_str = "∞"
            else:
                ratio_str = f"{ratio:6.1f}"
            print(f"│ {i:>4} │ {row['magasin']:>7} │ {row['deficit_total']:>9,.0f} │ {row['nb_items']:>5,} │ {ratio_str:>9} │")

        # Top matériels déficitaires
        print(f"\n🔧 TOP 10 MATÉRIELS DÉFICITAIRES")
        print("─" * 70)
        top_deficits = manager.deficit_analyzer.get_top_deficits(deficits_result, 10, by_abs_value=True)

        print("│ Rang │ Magasin │      Nomenclature      │  Déficit  │   Type   │")
        print("├──────┼─────────┼────────────────────────┼───────────┼──────────┤")
        for i, (_, row) in enumerate(top_deficits.iterrows(), 1):
            deficit = row['deficit']
            if deficit > 0:
                type_deficit = "Surplus"
            else:
                type_deficit = "Manque"
            print(f"│ {i:>4} │ {row['magasin']:>7} │ {row['nomenclature']:>22} │ {deficit:>9,.0f} │ {type_deficit:>8} │")

        # Fichiers créés
        output_dir = Path("deficits_output")
        if output_dir.exists():
            print(f"\n💾 FICHIERS CRÉÉS")
            print("─" * 50)
            files_created = list(output_dir.glob("*20250925_1722*"))
            for file in files_created:
                size_mb = file.stat().st_size / 1024
                if size_mb < 1:
                    size_str = f"{file.stat().st_size} B"
                elif size_mb < 1024:
                    size_str = f"{size_mb:.1f} KB"
                else:
                    size_str = f"{size_mb/1024:.1f} MB"

                print(f"✅ {file.name[:40]:<40} ({size_str:>8})")

        print(f"\n🎯 ACTIONS RECOMMANDÉES")
        print("─" * 50)
        print("1. Analyser les magasins avec les plus gros déficits")
        print("2. Vérifier les nomenclatures avec manque de stock (déficit négatif)")
        print("3. Réapprovisionner les matériels en manque de stock")
        print("4. Redistribuer les surplus de stock vers les magasins en manque")
        print("5. Consulter les fichiers Excel pour analyse détaillée")

        print(f"\n" + "─" * 80)
        print("✅ Analyse terminée - Fichiers disponibles dans 'deficits_output/'")
        print("─" * 80)

    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    display_deficits_summary()