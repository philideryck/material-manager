"""
Analyse spécifique des déficits de stock (-C) et matériels déficitaires.
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


def analyze_stock_deficits():
    """Analyse détaillée des magasins et matériels avec données -C déficitaires."""

    try:
        manager = MaterialManager()
        manager.load_data('./data/inventaire_court.csv')
        df_long = manager._transformed_data

        print_separator("ANALYSE DES DÉFICITS DE STOCK (-C)")

        # 1. MAGASINS AVEC DONNÉES -C (STOCK)
        print("🏢 MAGASINS AVEC DONNÉES DE STOCK (-C)")
        print("─" * 60)

        magasins_avec_stock = df_long[df_long['type_donnee'] == 'C']['magasin'].unique()
        magasins_avec_exploitation = df_long[df_long['type_donnee'] == 'U']['magasin'].unique()

        print(f"Magasins avec stock (-C)      : {len(magasins_avec_stock):2} magasins")
        print(f"Magasins avec exploitation (-U): {len(magasins_avec_exploitation):2} magasins")

        print(f"\n📋 Liste des magasins avec stock (-C):")
        print("   " + ", ".join(sorted(magasins_avec_stock)))

        # 2. ANALYSE DES STOCKS PAR MAGASIN
        print(f"\n📊 ANALYSE DÉTAILLÉE DES STOCKS PAR MAGASIN")
        print("─" * 80)

        stock_data = df_long[df_long['type_donnee'] == 'C'].copy()
        stock_summary = stock_data.groupby('magasin').agg({
            'nomenclature': 'nunique',
            'quantite': ['sum', 'mean', 'max', 'min', 'count']
        }).round(2)

        stock_summary.columns = ['nb_nomenclatures', 'stock_total', 'stock_moyen',
                               'stock_max', 'stock_min', 'nb_lignes']
        stock_summary = stock_summary.sort_values('stock_total', ascending=False)

        print("│ Magasin │ Nomenclatures │ Stock Total │ Stock Moyen │ Stock Max │ Lignes │")
        print("├─────────┼───────────────┼─────────────┼─────────────┼───────────┼────────┤")

        for magasin, row in stock_summary.iterrows():
            print(f"│ {magasin:>7} │ {row['nb_nomenclatures']:>13,} │ {row['stock_total']:>11,.0f} │ {row['stock_moyen']:>11.1f} │ {row['stock_max']:>9,.0f} │ {row['nb_lignes']:>6,} │")

        # 3. VRAIS DÉFICITS (avec comparaison U/C directe)
        print_separator("VRAIS DÉFICITS DE STOCK")

        # Charger les vrais déficits déjà calculés
        vrais_deficits_file = Path("deficits_output").glob("vrais_deficits_*.csv")
        latest_file = max(vrais_deficits_file, key=lambda x: x.stat().st_mtime, default=None)

        if latest_file:
            vrais_deficits = pd.read_csv(latest_file)
            print(f"📁 Données chargées depuis: {latest_file.name}")
        else:
            print("❌ Pas de fichier de vrais déficits trouvé, calcul en cours...")
            # Recalculer
            magasins_complets = ['ANTACL', 'BCE', 'BLD', 'BST', 'CGC', 'CHG', 'CNSO', 'MDM', 'MRC', 'PAU']
            df_complet = df_long[df_long['magasin'].isin(magasins_complets)]
            deficits_result = manager.deficit_analyzer.analyze_deficits(df_complet)
            vrais_deficits = deficits_result.data[
                (deficits_result.data['quantite_exploitation'] > 0) &
                (deficits_result.data['quantite_stock'] > 0)
            ].copy()

        # 4. ANALYSE DES MANQUES DE STOCK (déficit négatif)
        manques_stock = vrais_deficits[vrais_deficits['deficit'] < 0].copy()
        surplus_stock = vrais_deficits[vrais_deficits['deficit'] > 0].copy()

        print(f"🔴 MANQUES DE STOCK (exploitation > stock)")
        print("─" * 70)
        print(f"Cas de manques : {len(manques_stock):,}")
        print(f"Quantité manquante totale : {abs(manques_stock['deficit'].sum()):,.0f}")

        if len(manques_stock) > 0:
            print(f"\n🏢 MAGASINS AVEC LE PLUS DE MANQUES:")
            manques_par_magasin = manques_stock.groupby('magasin').agg({
                'deficit': ['count', 'sum'],
                'quantite_exploitation': 'sum',
                'quantite_stock': 'sum'
            }).round(0)
            manques_par_magasin.columns = ['nb_manques', 'deficit_total', 'total_exploitation', 'total_stock']
            manques_par_magasin['deficit_total'] = abs(manques_par_magasin['deficit_total'])
            manques_par_magasin = manques_par_magasin.sort_values('deficit_total', ascending=False)

            print("│ Magasin │ Nb Manques │ Manque Total │ Exploitation │ Stock │")
            print("├─────────┼────────────┼──────────────┼──────────────┼───────┤")
            for magasin, row in manques_par_magasin.iterrows():
                print(f"│ {magasin:>7} │ {row['nb_manques']:>10,.0f} │ {row['deficit_total']:>12,.0f} │ {row['total_exploitation']:>12,.0f} │ {row['total_stock']:>5,.0f} │")

            print(f"\n🔧 TOP 20 NOMENCLATURES EN MANQUE DE STOCK:")
            top_manques = manques_stock.sort_values('deficit').head(20)

            print("│ Rang │ Magasin │      Nomenclature      │ Exploitation │ Stock │  Manque │")
            print("├──────┼─────────┼────────────────────────┼──────────────┼───────┼─────────┤")
            for i, (_, row) in enumerate(top_manques.iterrows(), 1):
                manque = abs(row['deficit'])
                print(f"│ {i:>4} │ {row['magasin']:>7} │ {row['nomenclature']:>22} │ {row['quantite_exploitation']:>12,.0f} │ {row['quantite_stock']:>5,.0f} │ {manque:>7,.0f} │")

        # 5. ANALYSE DES SURPLUS DE STOCK (déficit positif)
        print(f"\n🟡 SURPLUS DE STOCK (stock > exploitation)")
        print("─" * 70)
        print(f"Cas de surplus : {len(surplus_stock):,}")
        print(f"Quantité surplus totale : {surplus_stock['deficit'].sum():,.0f}")

        if len(surplus_stock) > 0:
            print(f"\n🏢 MAGASINS AVEC LE PLUS DE SURPLUS:")
            surplus_par_magasin = surplus_stock.groupby('magasin').agg({
                'deficit': ['count', 'sum'],
                'quantite_exploitation': 'sum',
                'quantite_stock': 'sum'
            }).round(0)
            surplus_par_magasin.columns = ['nb_surplus', 'surplus_total', 'total_exploitation', 'total_stock']
            surplus_par_magasin = surplus_par_magasin.sort_values('surplus_total', ascending=False)

            print("│ Magasin │ Nb Surplus │ Surplus Total │ Exploitation │ Stock  │")
            print("├─────────┼────────────┼───────────────┼──────────────┼────────┤")
            for magasin, row in surplus_par_magasin.iterrows():
                print(f"│ {magasin:>7} │ {row['nb_surplus']:>10,.0f} │ {row['surplus_total']:>13,.0f} │ {row['total_exploitation']:>12,.0f} │ {row['total_stock']:>6,.0f} │")

            print(f"\n🔧 TOP 20 NOMENCLATURES EN SURPLUS DE STOCK:")
            top_surplus = surplus_stock.sort_values('deficit', ascending=False).head(20)

            print("│ Rang │ Magasin │      Nomenclature      │ Exploitation │  Stock │ Surplus │")
            print("├──────┼─────────┼────────────────────────┼──────────────┼────────┼─────────┤")
            for i, (_, row) in enumerate(top_surplus.iterrows(), 1):
                surplus = row['deficit']
                print(f"│ {i:>4} │ {row['magasin']:>7} │ {row['nomenclature']:>22} │ {row['quantite_exploitation']:>12,.0f} │ {row['quantite_stock']:>6,.0f} │ {surplus:>7,.0f} │")

        # 6. SAUVEGARDES
        print_separator("SAUVEGARDE DES RÉSULTATS")

        output_dir = Path("deficits_output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        # Sauvegarder résumé des stocks
        stock_summary_file = output_dir / f"resume_stocks_par_magasin_{timestamp}.csv"
        stock_summary.reset_index().to_csv(stock_summary_file, index=False, encoding='utf-8')

        # Sauvegarder manques de stock
        if len(manques_stock) > 0:
            manques_file = output_dir / f"manques_stock_detailles_{timestamp}.csv"
            manques_stock.to_csv(manques_file, index=False, encoding='utf-8')
            print(f"💾 Manques de stock détaillés: {manques_file.name}")

        # Sauvegarder surplus de stock
        if len(surplus_stock) > 0:
            surplus_file = output_dir / f"surplus_stock_detailles_{timestamp}.csv"
            surplus_stock.to_csv(surplus_file, index=False, encoding='utf-8')
            print(f"💾 Surplus de stock détaillés: {surplus_file.name}")

        print(f"💾 Résumé des stocks: {stock_summary_file.name}")

        print_separator("CONCLUSION")
        print("✅ Analyse des déficits de stock terminée")
        print(f"🎯 {len(manques_stock):,} manques et {len(surplus_stock):,} surplus identifiés")
        print("💡 Focus sur les comparaisons directes U/C uniquement")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_stock_deficits()