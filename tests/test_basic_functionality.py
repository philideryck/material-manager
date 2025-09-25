"""
Tests de base pour la fonctionnalité refactorisée.
"""
import unittest
import pandas as pd
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.manager import MaterialManager
from src.core.exceptions import MaterialManagerError, DataImportError
from src.data.importer import InventoryImporter
from src.data.transformer import InventoryTransformer


class TestBasicFunctionality(unittest.TestCase):
    """Tests de base pour les fonctionnalités principales."""

    def setUp(self):
        """Préparation des tests."""
        self.manager = MaterialManager()

    def test_manager_initialization(self):
        """Test de l'initialisation du manager."""
        self.assertIsNotNone(self.manager)
        self.assertIsInstance(self.manager.importer, InventoryImporter)
        self.assertIsInstance(self.manager.transformer, InventoryTransformer)
        self.assertFalse(self.manager.has_data)

    def test_importer_with_nonexistent_file(self):
        """Test de l'importation avec un fichier inexistant."""
        with self.assertRaises(DataImportError):
            self.manager.importer.import_csv("nonexistent_file.csv")

    def test_transformer_with_empty_dataframe(self):
        """Test de transformation avec un DataFrame vide."""
        empty_df = pd.DataFrame()
        with self.assertRaises(Exception):
            self.manager.transformer.transform_to_long(empty_df)

    def test_create_sample_data(self):
        """Test de création de données d'exemple."""
        # Créer des données d'exemple
        sample_data = pd.DataFrame({
            'NNO': ['ITEM001', 'ITEM002', 'ITEM003'],
            'MAG1-U': [10, 5, 0],
            'MAG1-C': [8, 6, 2],
            'MAG2-U': [15, 0, 3],
            'MAG2-C': [12, 4, 3]
        })

        # Transformer les données
        transformed = self.manager.transformer.transform_to_long(sample_data)

        # Vérifications
        self.assertFalse(transformed.empty)
        self.assertIn('nomenclature', transformed.columns)
        self.assertIn('magasin', transformed.columns)
        self.assertIn('type_donnee', transformed.columns)
        self.assertIn('quantite', transformed.columns)

        # Vérifier les types de données
        self.assertTrue(all(transformed['type_donnee'].isin(['U', 'C'])))
        self.assertTrue(all(transformed['quantite'] > 0))

    def test_deficit_analysis_with_sample_data(self):
        """Test d'analyse des déficits avec des données d'exemple."""
        sample_data = pd.DataFrame({
            'NNO': ['ITEM001', 'ITEM002'],
            'MAG1-U': [10, 5],
            'MAG1-C': [8, 6],
            'MAG2-U': [15, 0],
            'MAG2-C': [12, 4]
        })

        # Transformation et analyse
        transformed = self.manager.transformer.transform_to_long(sample_data)
        deficits = self.manager.deficit_analyzer.analyze_deficits(transformed)

        # Vérifications
        self.assertIsNotNone(deficits)
        self.assertIn('deficit', deficits.data.columns)
        self.assertIsInstance(deficits.summary, dict)

        # Vérifier qu'il y a des déficits calculés
        self.assertTrue('total_deficits' in deficits.summary)

    def test_stats_calculation_with_sample_data(self):
        """Test de calcul des statistiques avec des données d'exemple."""
        sample_data = pd.DataFrame({
            'NNO': ['ITEM001', 'ITEM002', 'ITEM003'],
            'MAG1-U': [10, 5, 8],
            'MAG1-C': [8, 6, 7],
            'MAG2-U': [15, 3, 2],
            'MAG2-C': [12, 4, 1]
        })

        transformed = self.manager.transformer.transform_to_long(sample_data)
        stats = self.manager.stats_analyzer.calculate_global_stats(transformed)

        # Vérifications
        self.assertIsNotNone(stats)
        self.assertGreater(stats.nombre_nomenclatures, 0)
        self.assertGreater(stats.nombre_magasins, 0)
        self.assertGreater(stats.quantite_totale, 0)

    def test_manager_without_data(self):
        """Test des méthodes du manager sans données chargées."""
        with self.assertRaises(MaterialManagerError):
            self.manager.calculate_global_statistics()

        with self.assertRaises(MaterialManagerError):
            self.manager.analyze_deficits()

        with self.assertRaises(MaterialManagerError):
            self.manager.get_top_magasins()


class TestDataTransformation(unittest.TestCase):
    """Tests spécifiques à la transformation des données."""

    def setUp(self):
        """Préparation des tests."""
        self.transformer = InventoryTransformer()

    def test_magasin_info_extraction(self):
        """Test de l'extraction des informations de magasin."""
        sample_data = pd.DataFrame({
            'NNO': ['ITEM001'],
            'MAGASIN_TEST-U': [10],
            'MAGASIN_TEST-C': [8]
        })

        transformed = self.transformer.transform_to_long(sample_data)

        # Vérifier l'extraction des noms de magasin
        self.assertIn('MAGASIN_TEST', transformed['magasin'].values)

        # Vérifier l'extraction des types
        self.assertIn('U', transformed['type_donnee'].values)
        self.assertIn('C', transformed['type_donnee'].values)

    def test_data_cleaning(self):
        """Test du nettoyage des données."""
        # Données avec valeurs problématiques
        sample_data = pd.DataFrame({
            'NNO': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004'],
            'MAG1-U': [10, None, '', 0],  # Valeurs problématiques
            'MAG1-C': [8, 5, 3, -1]       # Valeur négative
        })

        transformed = self.transformer.transform_to_long(sample_data)

        # Vérifier que les valeurs problématiques ont été supprimées
        self.assertTrue(all(transformed['quantite'] > 0))
        self.assertFalse(transformed['quantite'].isna().any())


class TestErrorHandling(unittest.TestCase):
    """Tests de gestion des erreurs."""

    def test_import_invalid_file_type(self):
        """Test d'importation d'un type de fichier invalide."""
        importer = InventoryImporter()

        # Créer un fichier temporaire avec une mauvaise extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            with self.assertRaises(DataImportError):
                importer.import_csv(tmp_path)
        finally:
            Path(tmp_path).unlink()

    def test_manager_error_propagation(self):
        """Test de la propagation des erreurs dans le manager."""
        manager = MaterialManager()

        # Test avec un chemin invalide
        with self.assertRaises(MaterialManagerError):
            manager.load_data("invalid_file.csv")


if __name__ == '__main__':
    print("🧪 Lancement des tests de base...")

    # Configuration du test runner pour plus de verbosité
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Résumé des résultats
    print(f"\n{'='*50}")
    print(f"📊 RÉSULTATS DES TESTS")
    print(f"{'='*50}")
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ ÉCHECS:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split('\\n')[-2]}")

    if result.errors:
        print(f"\n💥 ERREURS:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split('\\n')[-2]}")

    print(f"\n{'✅' if result.wasSuccessful() else '❌'} {'TOUS LES TESTS PASSENT' if result.wasSuccessful() else 'CERTAINS TESTS ÉCHOUENT'}")