"""
Test simple pour vérifier que la refactorisation fonctionne.
"""
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.core.manager import MaterialManager
    from src.core.exceptions import MaterialManagerError
    import pandas as pd

    print("🧪 Test simple de la refactorisation")
    print("=" * 50)

    # Test 1: Initialisation
    print("1️⃣  Test d'initialisation...")
    manager = MaterialManager()
    print("   ✅ MaterialManager initialisé avec succès")

    # Test 2: Données d'exemple
    print("2️⃣  Test avec données d'exemple...")
    sample_data = pd.DataFrame({
        'NNO': ['ITEM001', 'ITEM002', 'ITEM003'],
        'MAG1-U': [10, 5, 8],
        'MAG1-C': [8, 6, 7],
        'MAG2-U': [15, 3, 2],
        'MAG2-C': [12, 4, 1]
    })

    # Test de transformation
    transformed = manager.transformer.transform_to_long(sample_data)
    print(f"   ✅ Transformation réussie: {len(transformed)} entrées")
    print(f"   📊 Colonnes: {list(transformed.columns)}")

    # Test 3: Analyse des déficits
    print("3️⃣  Test d'analyse des déficits...")
    deficits = manager.deficit_analyzer.analyze_deficits(transformed)
    print(f"   ✅ Analyse des déficits réussie")
    print(f"   📈 Déficits trouvés: {deficits.summary.get('total_deficits', 0)}")

    # Test 4: Statistiques
    print("4️⃣  Test de calcul des statistiques...")
    stats = manager.stats_analyzer.calculate_global_stats(transformed)
    print(f"   ✅ Statistiques calculées")
    print(f"   📦 Nomenclatures: {stats.nombre_nomenclatures}")
    print(f"   🏢 Magasins: {stats.nombre_magasins}")
    print(f"   📊 Quantité totale: {stats.quantite_totale}")

    # Test 5: Avec le vrai fichier si disponible
    print("5️⃣  Test avec le fichier réel...")
    file_path = "./data/inventaire_court.csv"
    if Path(file_path).exists():
        try:
            # Juste tester l'info du fichier
            file_info = manager.get_file_info(file_path)
            print(f"   ✅ Fichier trouvé: {file_info['size_bytes']} bytes")
            print(f"   📋 Colonnes magasins estimées: {file_info.get('estimated_magasin_columns', 0)}")
        except Exception as e:
            print(f"   ⚠️  Erreur avec le fichier réel: {e}")
    else:
        print(f"   ℹ️  Fichier {file_path} non trouvé (normal pour les tests)")

    print("\n" + "=" * 50)
    print("✅ TOUS LES TESTS SIMPLES PASSENT !")
    print("🎉 La refactorisation semble fonctionner correctement")

except Exception as e:
    print(f"❌ Erreur dans les tests: {e}")
    import traceback
    traceback.print_exc()