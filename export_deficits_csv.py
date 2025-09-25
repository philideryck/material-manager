"""
Export CSV consolidé des déficits par magasins et nomenclatures.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.manager import MaterialManager


def create_comprehensive_csv_export():
    """Crée un export CSV complet des déficits par magasins et nomenclatures."""

    try:
        manager = MaterialManager()
        manager.load_data('./data/inventaire_court.csv')
        df_long = manager._transformed_data

        print("🔄 Génération de l'export CSV consolidé...")

        # 1. DÉFICITS PAR MAGASIN (RÉSUMÉ)
        print("   📊 Calcul des déficits par magasin...")

        # Ne considérer que les magasins avec données U ET C
        magasins_complets = ['ANTACL', 'BCE', 'BLD', 'BST', 'CGC', 'CHG', 'CNSO', 'MDM', 'MRC', 'PAU']
        df_complet = df_long[df_long['magasin'].isin(magasins_complets)]

        # Calculer les déficits
        deficits_result = manager.deficit_analyzer.analyze_deficits(df_complet)
        deficits_df = deficits_result.data

        # Filtrer pour les vrais déficits (avec U ET C > 0)
        vrais_deficits = deficits_df[
            (deficits_df['quantite_exploitation'] > 0) &
            (deficits_df['quantite_stock'] > 0)
        ].copy()

        # Résumé par magasin
        deficits_par_magasin = vrais_deficits.groupby('magasin').agg({
            'deficit': ['count', 'sum', 'mean', 'min', 'max'],
            'quantite_exploitation': ['sum', 'mean'],
            'quantite_stock': ['sum', 'mean'],
            'nomenclature': 'nunique'
        }).round(2)

        # Aplatir les colonnes
        deficits_par_magasin.columns = [
            'nb_deficits', 'deficit_total', 'deficit_moyen', 'deficit_min', 'deficit_max',
            'total_exploitation', 'moy_exploitation', 'total_stock', 'moy_stock',
            'nb_nomenclatures'
        ]

        # Ajouter des colonnes calculées
        deficits_par_magasin['nb_manques'] = vrais_deficits[vrais_deficits['deficit'] < 0].groupby('magasin').size().fillna(0).astype(int)
        deficits_par_magasin['nb_surplus'] = vrais_deficits[vrais_deficits['deficit'] > 0].groupby('magasin').size().fillna(0).astype(int)
        deficits_par_magasin['manques_total'] = abs(vrais_deficits[vrais_deficits['deficit'] < 0].groupby('magasin')['deficit'].sum().fillna(0))
        deficits_par_magasin['surplus_total'] = vrais_deficits[vrais_deficits['deficit'] > 0].groupby('magasin')['deficit'].sum().fillna(0)
        deficits_par_magasin['ratio_exploitation_stock'] = (deficits_par_magasin['total_exploitation'] /
                                                           (deficits_par_magasin['total_stock'] + 1)).round(3)

        # Trier par déficit total (valeur absolue)
        deficits_par_magasin['deficit_abs'] = abs(deficits_par_magasin['deficit_total'])
        deficits_par_magasin = deficits_par_magasin.sort_values('deficit_abs', ascending=False)
        deficits_par_magasin = deficits_par_magasin.drop('deficit_abs', axis=1)

        # 2. DÉFICITS PAR NOMENCLATURE (RÉSUMÉ)
        print("   🔧 Calcul des déficits par nomenclature...")

        deficits_par_nomenclature = vrais_deficits.groupby('nomenclature').agg({
            'deficit': ['count', 'sum', 'mean', 'min', 'max'],
            'quantite_exploitation': ['sum', 'mean'],
            'quantite_stock': ['sum', 'mean'],
            'magasin': 'nunique'
        }).round(2)

        # Aplatir les colonnes
        deficits_par_nomenclature.columns = [
            'nb_deficits', 'deficit_total', 'deficit_moyen', 'deficit_min', 'deficit_max',
            'total_exploitation', 'moy_exploitation', 'total_stock', 'moy_stock',
            'nb_magasins'
        ]

        # Ajouter des colonnes calculées
        deficits_par_nomenclature['nb_manques'] = vrais_deficits[vrais_deficits['deficit'] < 0].groupby('nomenclature').size().fillna(0).astype(int)
        deficits_par_nomenclature['nb_surplus'] = vrais_deficits[vrais_deficits['deficit'] > 0].groupby('nomenclature').size().fillna(0).astype(int)
        deficits_par_nomenclature['manques_total'] = abs(vrais_deficits[vrais_deficits['deficit'] < 0].groupby('nomenclature')['deficit'].sum().fillna(0))
        deficits_par_nomenclature['surplus_total'] = vrais_deficits[vrais_deficits['deficit'] > 0].groupby('nomenclature')['deficit'].sum().fillna(0)

        # Trier par déficit total (valeur absolue)
        deficits_par_nomenclature['deficit_abs'] = abs(deficits_par_nomenclature['deficit_total'])
        deficits_par_nomenclature = deficits_par_nomenclature.sort_values('deficit_abs', ascending=False)
        deficits_par_nomenclature = deficits_par_nomenclature.drop('deficit_abs', axis=1)

        # 3. DÉFICITS DÉTAILLÉS (LIGNE PAR LIGNE)
        print("   📋 Préparation des déficits détaillés...")

        # Ajouter des colonnes d'analyse
        vrais_deficits_detailles = vrais_deficits.copy()
        vrais_deficits_detailles['type_deficit'] = vrais_deficits_detailles['deficit'].apply(
            lambda x: 'MANQUE' if x < 0 else 'SURPLUS'
        )
        vrais_deficits_detailles['deficit_abs'] = abs(vrais_deficits_detailles['deficit'])
        vrais_deficits_detailles['ratio_exp_stock'] = (
            vrais_deficits_detailles['quantite_exploitation'] /
            (vrais_deficits_detailles['quantite_stock'] + 0.001)
        ).round(3)

        # Trier par déficit absolu
        vrais_deficits_detailles = vrais_deficits_detailles.sort_values('deficit_abs', ascending=False)

        # 4. EXPORT DES FICHIERS CSV
        output_dir = Path("deficits_output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        print("\n💾 Sauvegarde des fichiers CSV...")

        # Export déficits par magasin
        magasin_file = output_dir / f"DEFICITS_PAR_MAGASIN_{timestamp}.csv"
        deficits_par_magasin.reset_index().to_csv(magasin_file, index=False, encoding='utf-8', sep=';')
        print(f"✅ {magasin_file.name}")

        # Export déficits par nomenclature
        nomenclature_file = output_dir / f"DEFICITS_PAR_NOMENCLATURE_{timestamp}.csv"
        deficits_par_nomenclature.reset_index().to_csv(nomenclature_file, index=False, encoding='utf-8', sep=';')
        print(f"✅ {nomenclature_file.name}")

        # Export déficits détaillés
        detailles_file = output_dir / f"DEFICITS_DETAILLES_{timestamp}.csv"
        vrais_deficits_detailles.to_csv(detailles_file, index=False, encoding='utf-8', sep=';')
        print(f"✅ {detailles_file.name}")

        # 5. CRÉER UN FICHIER EXCEL AVEC PLUSIEURS ONGLETS
        print(f"📊 Création du fichier Excel consolidé...")
        excel_file = output_dir / f"DEFICITS_CONSOLIDÉS_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Onglet résumé
            summary_data = pd.DataFrame({
                'Métrique': [
                    'Total magasins analysés',
                    'Magasins avec données U et C',
                    'Comparaisons U/C possibles',
                    'Cas de manques (U > C)',
                    'Cas de surplus (C > U)',
                    'Déficit net (unités)',
                    'Total unités en manque',
                    'Total unités en surplus'
                ],
                'Valeur': [
                    42,
                    len(magasins_complets),
                    len(vrais_deficits),
                    len(vrais_deficits[vrais_deficits['deficit'] < 0]),
                    len(vrais_deficits[vrais_deficits['deficit'] > 0]),
                    vrais_deficits['deficit'].sum(),
                    abs(vrais_deficits[vrais_deficits['deficit'] < 0]['deficit'].sum()),
                    vrais_deficits[vrais_deficits['deficit'] > 0]['deficit'].sum()
                ]
            })
            summary_data.to_excel(writer, sheet_name='RÉSUMÉ', index=False)

            # Onglets principaux
            deficits_par_magasin.reset_index().to_excel(writer, sheet_name='DÉFICITS_PAR_MAGASIN', index=False)
            deficits_par_nomenclature.reset_index().to_excel(writer, sheet_name='DÉFICITS_PAR_NOMENCLATURE', index=False)
            vrais_deficits_detailles.to_excel(writer, sheet_name='DÉFICITS_DÉTAILLÉS', index=False)

            # Top manques et surplus
            top_manques = vrais_deficits[vrais_deficits['deficit'] < 0].sort_values('deficit').head(50)
            top_surplus = vrais_deficits[vrais_deficits['deficit'] > 0].sort_values('deficit', ascending=False).head(50)

            top_manques.to_excel(writer, sheet_name='TOP_50_MANQUES', index=False)
            top_surplus.to_excel(writer, sheet_name='TOP_50_SURPLUS', index=False)

        print(f"✅ {excel_file.name}")

        # 6. AFFICHER UN APERÇU DES RÉSULTATS
        print(f"\n📊 APERÇU DES RÉSULTATS")
        print("─" * 70)

        print(f"\n🏢 TOP 10 MAGASINS PAR DÉFICIT ABSOLU:")
        print("─" * 50)
        for i, (magasin, row) in enumerate(deficits_par_magasin.head(10).iterrows(), 1):
            deficit = row['deficit_total']
            type_def = "surplus" if deficit > 0 else "manque"
            print(f"{i:2}. {magasin:>7} : {abs(deficit):>8.0f} ({type_def})")

        print(f"\n🔧 TOP 10 NOMENCLATURES PAR DÉFICIT ABSOLU:")
        print("─" * 50)
        for i, (nomenclature, row) in enumerate(deficits_par_nomenclature.head(10).iterrows(), 1):
            deficit = row['deficit_total']
            type_def = "surplus" if deficit > 0 else "manque"
            print(f"{i:2}. {nomenclature:>22} : {abs(deficit):>6.0f} ({type_def})")

        print(f"\n📁 FICHIERS CRÉÉS DANS '{output_dir.name}/':")
        print("─" * 50)
        files = [magasin_file, nomenclature_file, detailles_file, excel_file]
        for file in files:
            size_kb = file.stat().st_size / 1024
            print(f"• {file.name:<40} ({size_kb:>6.1f} KB)")

        print(f"\n✅ EXPORT CSV CONSOLIDÉ TERMINÉ !")
        print(f"🎯 {len(vrais_deficits):,} déficits analysés sur {len(magasins_complets)} magasins")

        return magasin_file, nomenclature_file, detailles_file, excel_file

    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    create_comprehensive_csv_export()