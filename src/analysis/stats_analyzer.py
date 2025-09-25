"""
Module d'analyse des statistiques d'inventaire.
"""
import pandas as pd
from typing import Dict, Tuple
import logging

from ..core.exceptions import AnalysisError
from ..core.models import InventoryStats, AnalysisResult


logger = logging.getLogger(__name__)


class StatsAnalyzer:
    """Analyseur de statistiques pour les données d'inventaire."""

    def __init__(self):
        self._cache = {}

    def calculate_global_stats(self, df_long: pd.DataFrame, use_cache: bool = True) -> InventoryStats:
        """
        Calcule les statistiques globales de l'inventaire.

        Args:
            df_long: DataFrame au format long
            use_cache: Utiliser le cache

        Returns:
            Objet InventoryStats avec les statistiques

        Raises:
            AnalysisError: Si le calcul échoue
        """
        if df_long.empty:
            raise AnalysisError("DataFrame vide fourni pour le calcul des statistiques")

        cache_key = f"global_stats_{hash(str(df_long.values.tobytes()))}"
        if use_cache and cache_key in self._cache:
            logger.debug("Utilisation des statistiques en cache")
            return self._cache[cache_key]

        try:
            stats = InventoryStats(
                nombre_nomenclatures=df_long['nomenclature'].nunique(),
                nombre_magasins=df_long['magasin'].nunique(),
                nombre_total_entrees=len(df_long),
                quantite_totale=df_long['quantite'].sum(),
                quantite_moyenne=df_long['quantite'].mean(),
                quantite_mediane=df_long['quantite'].median(),
                quantite_max=df_long['quantite'].max(),
                quantite_min=df_long['quantite'].min()
            )

            if use_cache:
                self._cache[cache_key] = stats

            logger.info(f"Statistiques globales calculées: "
                       f"{stats.nombre_nomenclatures} nomenclatures, "
                       f"{stats.nombre_magasins} magasins")

            return stats

        except Exception as e:
            raise AnalysisError(f"Erreur lors du calcul des statistiques: {e}")

    def get_top_nomenclatures(self, df_long: pd.DataFrame, n: int = 10) -> AnalysisResult:
        """
        Retourne les top nomenclatures par quantité.

        Args:
            df_long: DataFrame au format long
            n: Nombre de nomenclatures à retourner

        Returns:
            AnalysisResult avec les top nomenclatures
        """
        if df_long.empty:
            return AnalysisResult(
                data=pd.DataFrame(columns=['nomenclature', 'quantite']),
                summary={'top_count': 0}
            )

        top_nomenclatures = (df_long.groupby('nomenclature')['quantite']
                           .sum()
                           .sort_values(ascending=False)
                           .head(n)
                           .reset_index())

        summary = {
            'top_count': len(top_nomenclatures),
            'total_quantity': top_nomenclatures['quantite'].sum(),
            'percentage_of_total': (top_nomenclatures['quantite'].sum() /
                                  df_long['quantite'].sum() * 100)
        }

        return AnalysisResult(data=top_nomenclatures, summary=summary)

    def get_top_magasins(self, df_long: pd.DataFrame, n: int = 10) -> AnalysisResult:
        """
        Retourne les top magasins par quantité.

        Args:
            df_long: DataFrame au format long
            n: Nombre de magasins à retourner

        Returns:
            AnalysisResult avec les top magasins
        """
        if df_long.empty:
            return AnalysisResult(
                data=pd.DataFrame(columns=['magasin', 'quantite']),
                summary={'top_count': 0}
            )

        top_magasins = (df_long.groupby('magasin')['quantite']
                       .sum()
                       .sort_values(ascending=False)
                       .head(n)
                       .reset_index())

        summary = {
            'top_count': len(top_magasins),
            'total_quantity': top_magasins['quantite'].sum(),
            'percentage_of_total': (top_magasins['quantite'].sum() /
                                  df_long['quantite'].sum() * 100)
        }

        return AnalysisResult(data=top_magasins, summary=summary)

    def analyze_distribution(self, df_long: pd.DataFrame) -> Dict[str, any]:
        """
        Analyse la distribution des quantités.

        Args:
            df_long: DataFrame au format long

        Returns:
            Dictionnaire avec les statistiques de distribution
        """
        if df_long.empty:
            return {'error': 'Pas de données à analyser'}

        quantites = df_long['quantite']

        # Calcul des percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = quantites.quantile([p/100 for p in percentiles])

        # Détection des outliers (méthode IQR)
        Q1 = quantites.quantile(0.25)
        Q3 = quantites.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = quantites[(quantites < lower_bound) | (quantites > upper_bound)]

        return {
            'percentiles': {f'p{p}': percentile_values[p/100] for p in percentiles},
            'outliers': {
                'count': len(outliers),
                'percentage': len(outliers) / len(quantites) * 100,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            },
            'distribution_stats': {
                'skewness': quantites.skew(),
                'kurtosis': quantites.kurtosis(),
                'std_dev': quantites.std(),
                'variance': quantites.var()
            }
        }

    def compare_exploitation_vs_stock(self, df_long: pd.DataFrame) -> AnalysisResult:
        """
        Compare les quantités totales entre exploitation (U) et stock (C).

        Args:
            df_long: DataFrame au format long

        Returns:
            AnalysisResult avec la comparaison
        """
        if df_long.empty or 'type_donnee' not in df_long.columns:
            return AnalysisResult(
                data=pd.DataFrame(),
                summary={'error': 'Données insuffisantes pour la comparaison'}
            )

        # Grouper par magasin et type
        comparison = (df_long.groupby(['magasin', 'type_donnee'])['quantite']
                     .sum()
                     .unstack(fill_value=0))

        # S'assurer que les colonnes U et C existent
        if 'U' not in comparison.columns:
            comparison['U'] = 0
        if 'C' not in comparison.columns:
            comparison['C'] = 0

        # Calculer les ratios et différences
        comparison['ratio_U_C'] = comparison['U'] / (comparison['C'] + 1)  # +1 pour éviter division par 0
        comparison['difference'] = comparison['U'] - comparison['C']
        comparison['difference_abs'] = abs(comparison['difference'])

        # Calculer le résumé
        summary = {
            'total_exploitation': comparison['U'].sum(),
            'total_stock': comparison['C'].sum(),
            'ratio_global': comparison['U'].sum() / (comparison['C'].sum() + 1),
            'magasins_surexploitation': (comparison['ratio_U_C'] > 1.1).sum(),
            'magasins_sous_exploitation': (comparison['ratio_U_C'] < 0.9).sum(),
            'magasins_equilibres': ((comparison['ratio_U_C'] >= 0.9) &
                                   (comparison['ratio_U_C'] <= 1.1)).sum()
        }

        result_df = comparison.reset_index().sort_values('difference_abs', ascending=False)

        return AnalysisResult(data=result_df, summary=summary)

    def get_magasin_details(self, df_long: pd.DataFrame, magasin: str) -> Dict[str, any]:
        """
        Obtient les détails d'un magasin spécifique.

        Args:
            df_long: DataFrame au format long
            magasin: Nom du magasin

        Returns:
            Dictionnaire avec les détails du magasin
        """
        magasin_data = df_long[df_long['magasin'] == magasin]

        if magasin_data.empty:
            return {'error': f'Aucune donnée trouvée pour le magasin {magasin}'}

        # Séparer exploitation et stock
        exploitation = magasin_data[magasin_data['type_donnee'] == 'U']
        stock = magasin_data[magasin_data['type_donnee'] == 'C']

        return {
            'magasin': magasin,
            'total_nomenclatures': magasin_data['nomenclature'].nunique(),
            'total_entries': len(magasin_data),
            'exploitation': {
                'count': len(exploitation),
                'total_quantity': exploitation['quantite'].sum(),
                'nomenclatures': exploitation['nomenclature'].nunique()
            },
            'stock': {
                'count': len(stock),
                'total_quantity': stock['quantite'].sum(),
                'nomenclatures': stock['nomenclature'].nunique()
            },
            'top_nomenclatures': (magasin_data.groupby('nomenclature')['quantite']
                                .sum()
                                .sort_values(ascending=False)
                                .head(5)
                                .to_dict())
        }

    def clear_cache(self) -> None:
        """Vide le cache d'analyse."""
        self._cache.clear()
        logger.info("Cache d'analyse statistique vidé")