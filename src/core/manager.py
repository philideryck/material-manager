"""
Gestionnaire principal pour l'analyse des matériels.
"""
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Dict, Any

from .exceptions import MaterialManagerError, ConfigurationError
from .models import InventoryStats, AnalysisResult
from ..data.importer import InventoryImporter
from ..data.transformer import InventoryTransformer
from ..analysis.deficit_analyzer import DeficitAnalyzer
from ..analysis.stats_analyzer import StatsAnalyzer
from ..visualization.charts import InventoryCharts


logger = logging.getLogger(__name__)


class MaterialManager:
    """
    Gestionnaire principal pour l'analyse des données de matériel.

    Cette classe orchestre toutes les opérations d'import, transformation,
    analyse et visualisation des données d'inventaire.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le gestionnaire de matériel.

        Args:
            config: Configuration optionnelle
        """
        self.config = config or {}
        self._setup_logging()

        # Initialiser les composants
        self.importer = InventoryImporter()
        self.transformer = InventoryTransformer()
        self.deficit_analyzer = DeficitAnalyzer()
        self.stats_analyzer = StatsAnalyzer()
        self.charts = InventoryCharts()

        # Données
        self._raw_data: Optional[pd.DataFrame] = None
        self._transformed_data: Optional[pd.DataFrame] = None

        logger.info("MaterialManager initialisé")

    def _setup_logging(self) -> None:
        """Configure le système de logging."""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def load_data(self, file_path: str) -> None:
        """
        Charge et transforme les données depuis un fichier.

        Args:
            file_path: Chemin vers le fichier de données

        Raises:
            MaterialManagerError: Si le chargement échoue
        """
        try:
            logger.info(f"Chargement des données depuis: {file_path}")

            # Importation
            self._raw_data = self.importer.import_csv(file_path)

            # Transformation
            self._transformed_data = self.transformer.transform_to_long(self._raw_data)

            logger.info("Données chargées et transformées avec succès")

        except Exception as e:
            raise MaterialManagerError(f"Erreur lors du chargement des données: {e}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtient des informations sur un fichier sans le charger complètement.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Dictionnaire avec les informations du fichier
        """
        return self.importer.get_file_info(file_path)

    def get_data_overview(self) -> Dict[str, Any]:
        """
        Retourne un aperçu des données chargées.

        Returns:
            Dictionnaire avec l'aperçu des données

        Raises:
            MaterialManagerError: Si aucune donnée n'est chargée
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée. Utilisez load_data() d'abord.")

        df = self._transformed_data

        return {
            'raw_shape': self._raw_data.shape,
            'transformed_shape': df.shape,
            'nomenclatures_count': df['nomenclature'].nunique(),
            'magasins_count': df['magasin'].nunique(),
            'total_quantity': df['quantite'].sum(),
            'exploitation_entries': len(df[df['type_donnee'] == 'U']),
            'stock_entries': len(df[df['type_donnee'] == 'C']),
            'sample_data': df.head(3).to_dict('records')
        }

    def calculate_global_statistics(self) -> InventoryStats:
        """
        Calcule les statistiques globales.

        Returns:
            Objet InventoryStats

        Raises:
            MaterialManagerError: Si aucune donnée n'est chargée
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.stats_analyzer.calculate_global_stats(self._transformed_data)

    def analyze_deficits(self) -> AnalysisResult:
        """
        Analyse les déficits entre exploitation et stock.

        Returns:
            AnalysisResult avec les déficits

        Raises:
            MaterialManagerError: Si aucune donnée n'est chargée
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.deficit_analyzer.analyze_deficits(self._transformed_data)

    def get_top_magasins(self, n: int = 10) -> AnalysisResult:
        """
        Obtient les top magasins par quantité.

        Args:
            n: Nombre de magasins à retourner

        Returns:
            AnalysisResult avec les top magasins
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.stats_analyzer.get_top_magasins(self._transformed_data, n)

    def get_top_nomenclatures(self, n: int = 10) -> AnalysisResult:
        """
        Obtient les top nomenclatures par quantité.

        Args:
            n: Nombre de nomenclatures à retourner

        Returns:
            AnalysisResult avec les top nomenclatures
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.stats_analyzer.get_top_nomenclatures(self._transformed_data, n)

    def compare_exploitation_vs_stock(self) -> AnalysisResult:
        """
        Compare les quantités exploitation vs stock.

        Returns:
            AnalysisResult avec la comparaison
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.stats_analyzer.compare_exploitation_vs_stock(self._transformed_data)

    def get_magasin_details(self, magasin: str) -> Dict[str, Any]:
        """
        Obtient les détails d'un magasin.

        Args:
            magasin: Nom du magasin

        Returns:
            Dictionnaire avec les détails
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.stats_analyzer.get_magasin_details(self._transformed_data, magasin)

    def filter_by_magasin(self, magasin: str) -> pd.DataFrame:
        """
        Filtre les données pour un magasin.

        Args:
            magasin: Nom du magasin

        Returns:
            DataFrame filtré
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.transformer.filter_by_magasin(self._transformed_data, magasin)

    def filter_by_nomenclature(self, nomenclature: str) -> pd.DataFrame:
        """
        Filtre les données pour une nomenclature.

        Args:
            nomenclature: Code de nomenclature

        Returns:
            DataFrame filtré
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        return self.transformer.filter_by_nomenclature(self._transformed_data, nomenclature)

    def export_data(self, output_path: str, data_type: str = 'transformed',
                   format: str = 'csv') -> None:
        """
        Exporte les données.

        Args:
            output_path: Chemin de sortie
            data_type: Type de données ('raw', 'transformed', 'deficits')
            format: Format d'export ('csv', 'excel')

        Raises:
            MaterialManagerError: Si l'export échoue
        """
        try:
            if data_type == 'raw':
                if self._raw_data is None:
                    raise MaterialManagerError("Aucune donnée brute disponible")
                data = self._raw_data
            elif data_type == 'transformed':
                if self._transformed_data is None:
                    raise MaterialManagerError("Aucune donnée transformée disponible")
                data = self._transformed_data
            elif data_type == 'deficits':
                deficit_result = self.analyze_deficits()
                data = deficit_result.data
            else:
                raise MaterialManagerError(f"Type de données non supporté: {data_type}")

            # Export
            output_path = Path(output_path)
            if format == 'csv':
                data.to_csv(output_path, index=False, encoding='utf-8')
            elif format == 'excel':
                data.to_excel(output_path, index=False)
            else:
                raise MaterialManagerError(f"Format non supporté: {format}")

            logger.info(f"Données exportées vers: {output_path}")

        except Exception as e:
            raise MaterialManagerError(f"Erreur lors de l'export: {e}")

    def generate_visualizations(self, output_dir: Optional[str] = None) -> None:
        """
        Génère toutes les visualisations.

        Args:
            output_dir: Répertoire de sortie pour sauvegarder les graphiques
        """
        if self._transformed_data is None:
            raise MaterialManagerError("Aucune donnée chargée.")

        try:
            output_path = Path(output_dir) if output_dir else None

            # Top magasins
            top_magasins = self.get_top_magasins(15)
            save_path = output_path / "top_magasins.png" if output_path else None
            self.charts.plot_top_magasins(top_magasins, save_path=save_path)

            # Top nomenclatures
            top_nomenclatures = self.get_top_nomenclatures(10)
            save_path = output_path / "top_nomenclatures.png" if output_path else None
            self.charts.plot_top_nomenclatures(top_nomenclatures, save_path=save_path)

            # Distribution
            save_path = output_path / "distribution.png" if output_path else None
            self.charts.plot_distribution(self._transformed_data, save_path=save_path)

            # Comparaison exploitation vs stock
            comparison = self.compare_exploitation_vs_stock()
            save_path = output_path / "exploitation_vs_stock.png" if output_path else None
            self.charts.plot_exploitation_vs_stock(comparison, save_path=save_path)

            # Heatmap des déficits
            deficits = self.analyze_deficits()
            save_path = output_path / "deficit_heatmap.png" if output_path else None
            self.charts.plot_deficit_heatmap(deficits, save_path=save_path)

            logger.info("Toutes les visualisations ont été générées")

        except Exception as e:
            raise MaterialManagerError(f"Erreur lors de la génération des visualisations: {e}")

    def clear_cache(self) -> None:
        """Vide tous les caches."""
        self.transformer.clear_cache()
        self.deficit_analyzer.clear_cache()
        self.stats_analyzer.clear_cache()
        logger.info("Tous les caches vidés")

    def get_available_magasins(self) -> list:
        """Retourne la liste des magasins disponibles."""
        if self._transformed_data is None:
            return []
        return sorted(self._transformed_data['magasin'].unique().tolist())

    def get_available_nomenclatures(self) -> list:
        """Retourne la liste des nomenclatures disponibles."""
        if self._transformed_data is None:
            return []
        return sorted(self._transformed_data['nomenclature'].unique().tolist())

    @property
    def has_data(self) -> bool:
        """Vérifie si des données sont chargées."""
        return self._transformed_data is not None and not self._transformed_data.empty