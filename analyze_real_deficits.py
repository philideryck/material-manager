"""
Analyse des vrais déficits - seulement les cas avec données U ET C présentes.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.manager import MaterialManager


def print_separator(title: str = "", width: int = 80) -> None:
    """Affiche un séparateur avec titre optionnel."""
    print("=" * width)
    if title:
        print(f" {title} ".center(width, "="))
        print("=" * width)


def analyze_real_deficits():
    """Analyse des déficits réels uniquement (avec U ET C présents)."""

    try:
        manager = MaterialManager()
        manager.load_data('./data/inventaire_court.csv')

        # Obtenir les données transformées
        df_long = manager._transformed_data

        print_separator("ANALYSE DES VRAIS DÉFICITS (U ET C PRÉSENTS)")

        # Analyser la disponibilité des données par magasin
        print("📊 RÉPARTITION DES DONNÉES PAR MAGASIN")
        print("─" * 60)

        magasin_stats = df_long.groupby('magasin').agg({
            'type_donnee': lambda x: list(x.unique()),
            'nomenclature': 'nunique',
            'quantite': 'sum'
        }).reset_index()

        magasin_stats.columns = ['magasin', 'types_donnees', 'nb_nomenclatures', 'quantite_totale']

        # Identifier les magasins avec U seulement, C seulement, ou U ET C
        magasin_stats['has_U'] = magasin_stats['types_donnees'].apply(lambda x: 'U' in x)
        magasin_stats['has_C'] = magasin_stats['types_donnees'].apply(lambda x: 'C' in x)
        magasin_stats['has_both'] = magasin_stats['has_U'] & magasin_stats['has_C']

        print("│ Type de données │ Nb Magasins │")
        print("├─────────────────┼─────────────┤")
        print(f"│ U seulement     │ {(magasin_stats['has_U'] & ~magasin_stats['has_C']).sum():>11} │")
        print(f"│ C seulement     │ {(~magasin_stats['has_U'] & magasin_stats['has_C']).sum():>11} │")
        print(f"│ U ET C          │ {magasin_stats['has_both'].sum():>11} │")

        # Afficher les magasins par catégorie
        u_only = magasin_stats[magasin_stats['has_U'] & ~magasin_stats['has_C']]['magasin'].tolist()
        c_only = magasin_stats[~magasin_stats['has_U'] & magasin_stats['has_C']]['magasin'].tolist()
        both = magasin_stats[magasin_stats['has_both']]['magasin'].tolist()

        print(f"\n🔵 MAGASINS AVEC EXPLOITATION SEULEMENT (-U) : {len(u_only)}")
        if u_only:
            print("   " + ", ".join(sorted(u_only)))

        print(f"\n🟡 MAGASINS AVEC STOCK SEULEMENT (-C) : {len(c_only)}")
        if c_only:
            print("   " + ", ".join(sorted(c_only)))

        print(f"\n🟢 MAGASINS AVEC EXPLOITATION ET STOCK (-U ET -C) : {len(both)}")
        if both:
            print("   " + ", ".join(sorted(both)))

        # Maintenant analyser les vrais déficits (seulement U ET C)
        print_separator("VRAIS DÉFICITS (MAGASINS AVEC U ET C)")

        # Filtrer pour ne garder que les magasins avec les deux types de données
        magasins_complets = magasin_stats[magasin_stats['has_both']]['magasin'].tolist()

        if not magasins_complets:
            print("❌ Aucun magasin n'a à la fois des données U et C !")
            return

        df_complet = df_long[df_long['magasin'].isin(magasins_complets)]

        print(f"📈 Analyse sur {len(magasins_complets)} magasins complets")

        # Analyser les déficits pour ces magasins seulement
        deficits_result = manager.deficit_analyzer.analyze_deficits(df_complet)
        deficits_df = deficits_result.data
        summary = deficits_result.summary

        # Filtrer pour ne garder que les vrais déficits (pas les zéros)
        vrais_deficits = deficits_df[
            (deficits_df['quantite_exploitation'] > 0) &
            (deficits_df['quantite_stock'] > 0)
        ].copy()

        print(f"🎯 Nombre de comparaisons U/C directes : {len(vrais_deficits):,}")

        if vrais_deficits.empty:
            print("❌ Aucune comparaison directe U/C trouvée (même nomenclature dans même magasin)")

            # Analyser pourquoi
            print("\n🔍 ANALYSE DÉTAILLÉE DES MAGASINS COMPLETS")
            for magasin in sorted(magasins_complets):
                mag_data = df_complet[df_complet['magasin'] == magasin]
                u_data = mag_data[mag_data['type_donnee'] == 'U']
                c_data = mag_data[mag_data['type_donnee'] == 'C']

                print(f"\n📋 {magasin}:")
                print(f"   Nomenclatures U: {u_data['nomenclature'].nunique():,}")
                print(f"   Nomenclatures C: {c_data['nomenclature'].nunique():,}")

                # Intersection
                u_nomenclatures = set(u_data['nomenclature'])
                c_nomenclatures = set(c_data['nomenclature'])
                intersection = u_nomenclatures & c_nomenclatures

                print(f"   Nomenclatures communes: {len(intersection):,}")
                if len(intersection) > 0:
                    print(f"   Exemples communes: {list(intersection)[:5]}")

            return

        print(f"\n📊 RÉSUMÉ DES VRAIS DÉFICITS")
        print("─" * 50)

        surplus_vrais = vrais_deficits[vrais_deficits['deficit'] > 0]
        manque_vrais = vrais_deficits[vrais_deficits['deficit'] < 0]

        print(f"Surplus réels (C > U)     : {len(surplus_vrais):,} cas")
        print(f"Manque réel (U > C)       : {len(manque_vrais):,} cas")
        print(f"Déficit total réel        : {vrais_deficits['deficit'].sum():,.0f}")

        # Top déficits réels
        if len(vrais_deficits) > 0:
            print(f"\n🔧 TOP 15 VRAIS DÉFICITS")
            print("─" * 80)

            top_vrais = vrais_deficits.copy()
            top_vrais['deficit_abs'] = abs(top_vrais['deficit'])
            top_vrais = top_vrais.sort_values('deficit_abs', ascending=False)

            print("│ Magasin │      Nomenclature      │ Exploitation │ Stock │ Déficit │ Type    │")
            print("├─────────┼────────────────────────┼──────────────┼───────┼─────────┼─────────┤")

            for _, row in top_vrais.head(15).iterrows():
                deficit = row['deficit']
                type_def = "Surplus" if deficit > 0 else "Manque"
                print(f"│ {row['magasin']:>7} │ {row['nomenclature']:>22} │ {row['quantite_exploitation']:>12,.0f} │ {row['quantite_stock']:>5,.0f} │ {deficit:>7,.0f} │ {type_def:<7} │")

        # Sauvegarder les vrais déficits
        output_dir = Path("deficits_output")
        output_dir.mkdir(exist_ok=True)

        vrais_deficits_file = output_dir / f"vrais_deficits_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        vrais_deficits.to_csv(vrais_deficits_file, index=False, encoding='utf-8')

        print(f"\n💾 Vrais déficits sauvegardés: {vrais_deficits_file}")
        print(f"   Contient {len(vrais_deficits):,} comparaisons directes U/C")

        # Analyser les nomenclatures les plus problématiques
        if len(vrais_deficits) > 0:
            print(f"\n🎯 NOMENCLATURES LES PLUS DÉFICITAIRES (réelles)")
            print("─" * 70)

            nomencl_deficit = vrais_deficits.groupby('nomenclature').agg({
                'deficit': ['sum', 'count', 'mean'],
                'quantite_exploitation': 'sum',
                'quantite_stock': 'sum'
            }).round(2)

            nomencl_deficit.columns = ['deficit_total', 'nb_magasins', 'deficit_moyen',
                                     'total_exploitation', 'total_stock']
            nomencl_deficit = nomencl_deficit.sort_values('deficit_total', key=abs, ascending=False)

            print(nomencl_deficit.head(10).to_string())

            # Sauvegarder
            nomencl_file = output_dir / f"nomenclatures_vrais_deficits_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            nomencl_deficit.reset_index().to_csv(nomencl_file, index=False, encoding='utf-8')
            print(f"\n💾 Nomenclatures déficitaires sauvegardées: {nomencl_file}")

        print_separator("ANALYSE TERMINÉE")
        print("✅ Analyse des vrais déficits terminée")
        print("💡 Seules les comparaisons directes U/C ont été considérées")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_real_deficits()