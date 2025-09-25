"""
Test pour vérifier l'inversion du calcul de déficit.
"""
import sys
from pathlib import Path
import pandas as pd

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.manager import MaterialManager

def test_deficit_inversion():
    """Test pour vérifier que le déficit est maintenant calculé comme Stock - Exploitation."""

    print("🧪 Test de l'inversion du calcul de déficit")
    print("=" * 60)

    # Créer des données d'exemple simples
    sample_data = pd.DataFrame({
        'NNO': ['ITEM001', 'ITEM002', 'ITEM003'],
        'MAG1-U': [10, 5, 15],     # Exploitation
        'MAG1-C': [8, 10, 12],     # Stock
    })

    print("📊 Données de test:")
    print("ITEM001: Exploitation=10, Stock=8  -> Déficit attendu = 8-10 = -2 (manque)")
    print("ITEM002: Exploitation=5,  Stock=10 -> Déficit attendu = 10-5 = +5 (surplus)")
    print("ITEM003: Exploitation=15, Stock=12 -> Déficit attendu = 12-15 = -3 (manque)")

    # Initialiser le manager et vider le cache
    manager = MaterialManager()
    manager.clear_cache()

    # Transformer et analyser
    transformed = manager.transformer.transform_to_long(sample_data)
    print(f"\n📋 Données transformées:")
    print(transformed.to_string(index=False))

    # Analyser les déficits directement avec l'analyseur
    deficits_result = manager.deficit_analyzer.analyze_deficits(transformed)
    deficits_df = deficits_result.data

    print(f"\n🔍 Résultats de l'analyse des déficits:")
    print(deficits_df.to_string(index=False))

    print(f"\n📈 Résumé:")
    summary = deficits_result.summary
    print(f"   Surplus de stock: {summary.get('surplus_stock_count', 0)} cas")
    print(f"   Manque de stock: {summary.get('manque_stock_count', 0)} cas")

    # Vérifications
    print(f"\n✅ Vérifications:")

    # ITEM001: doit avoir déficit = -2 (manque)
    item001_deficit = deficits_df[deficits_df['nomenclature'] == 'ITEM001']['deficit'].iloc[0]
    print(f"   ITEM001 déficit: {item001_deficit} (attendu: -2)")
    assert item001_deficit == -2, f"Erreur: déficit ITEM001 = {item001_deficit}, attendu -2"

    # ITEM002: doit avoir déficit = +5 (surplus)
    item002_deficit = deficits_df[deficits_df['nomenclature'] == 'ITEM002']['deficit'].iloc[0]
    print(f"   ITEM002 déficit: {item002_deficit} (attendu: +5)")
    assert item002_deficit == 5, f"Erreur: déficit ITEM002 = {item002_deficit}, attendu +5"

    # ITEM003: doit avoir déficit = -3 (manque)
    item003_deficit = deficits_df[deficits_df['nomenclature'] == 'ITEM003']['deficit'].iloc[0]
    print(f"   ITEM003 déficit: {item003_deficit} (attendu: -3)")
    assert item003_deficit == -3, f"Erreur: déficit ITEM003 = {item003_deficit}, attendu -3"

    print(f"\n🎉 Toutes les vérifications passent !")
    print(f"✅ Le déficit est maintenant calculé comme: Stock - Exploitation")
    print(f"   • Déficit positif = Surplus de stock")
    print(f"   • Déficit négatif = Manque de stock")

if __name__ == "__main__":
    try:
        test_deficit_inversion()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()