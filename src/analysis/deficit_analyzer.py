"""
Module d'analyse des déficits entre exploitation et stock.
"""
import pandas as pd
from typing import Dict, List
import logging

from ..core.exceptions import AnalysisError
from ..core.models import DeficitItem, AnalysisResult


logger = logging.getLogger(__name__)


class DeficitAnalyzer:
    """Analyseur des déficits entre données d'exploitation (U) et de stock (C)."""

    def __init__(self):
        self._cache = {}

    def analyze_deficits(self, df_long: pd.DataFrame, use_cache: bool = True) -> AnalysisResult:
        """
        Analyse les déficits entre exploitation et stock.

        Args:
            df_long: DataFrame au format long
            use_cache: Utiliser le cache

        Returns:
            AnalysisResult contenant les déficits et statistiques

        Raises:
            AnalysisError: Si l'analyse échoue
        """
        if df_long.empty:
            raise AnalysisError("DataFrame vide fourni pour l'analyse des déficits")

        # Vérification du cache
        cache_key = f"deficit_{hash(str(df_long.values.tobytes()))}"
        if use_cache and cache_key in self._cache:
            logger.debug("Utilisation des résultats d'analyse en cache")
            return self._cache[cache_key]

        try:
            # Séparer les données d'exploitation et de stock
            exploitation_df = df_long[df_long['type_donnee'] == 'U'].copy()
            stock_df = df_long[df_long['type_donnee'] == 'C'].copy()

            if exploitation_df.empty and stock_df.empty:
                logger.warning("Aucune donnée d'exploitation ou de stock trouvée")
                return AnalysisResult(
                    data=pd.DataFrame(columns=['magasin', 'nomenclature', 'quantite_exploitation',
                                             'quantite_stock', 'deficit']),
                    summary={'total_deficits': 0, 'magasins_concernes': 0}
                )

            # Fusionner les données
            deficits_df = self._merge_exploitation_stock(exploitation_df, stock_df)

            # Calculer les statistiques
            summary = self._calculate_deficit_stats(deficits_df)

            result = AnalysisResult(
                data=deficits_df,
                summary=summary,
                metadata={
                    'exploitation_entries': len(exploitation_df),
                    'stock_entries': len(stock_df),
                    'analysis_type': 'deficit_analysis'
                }
            )

            # Mise en cache
            if use_cache:
                self._cache[cache_key] = result

            logger.info(f"Analyse des déficits terminée: {len(deficits_df)} déficits analysés")
            return result

        except Exception as e:
            raise AnalysisError(f"Erreur lors de l'analyse des déficits: {e}")

    def _merge_exploitation_stock(self, exploitation_df: pd.DataFrame,
                                 stock_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fusionne les données d'exploitation et de stock.

        Args:
            exploitation_df: DataFrame des données d'exploitation
            stock_df: DataFrame des données de stock

        Returns:
            DataFrame avec déficits calculés
        """
        # Merger sur magasin et nomenclature
        merged = exploitation_df.merge(
            stock_df,
            on=['magasin', 'nomenclature'],
            suffixes=('_exploitation', '_stock'),
            how='outer'
        )

        # Gérer les valeurs manquantes
        merged['quantite_exploitation'] = merged['quantite_exploitation'].fillna(0)
        merged['quantite_stock'] = merged['quantite_stock'].fillna(0)

        # Calculer le déficit (Stock - Exploitation)
        # Déficit positif = surplus de stock, déficit négatif = manque de stock
        merged['deficit'] = merged['quantite_stock'] - merged['quantite_exploitation']

        # Sélectionner les colonnes importantes
        result = merged[['magasin', 'nomenclature', 'quantite_exploitation',
                        'quantite_stock', 'deficit']].copy()

        # Trier par magasin puis nomenclature
        return result.sort_values(['magasin', 'nomenclature']).reset_index(drop=True)

    def _calculate_deficit_stats(self, deficits_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule les statistiques sur les déficits.

        Args:
            deficits_df: DataFrame contenant les déficits

        Returns:
            Dictionnaire des statistiques
        """
        if deficits_df.empty:
            return {
                'total_deficits': 0,
                'deficit_total': 0.0,
                'deficit_moyen': 0.0,
                'magasins_concernes': 0,
                'surplus_total': 0.0,
                'sous_exploitation_total': 0.0
            }

        # Filtrer les déficits non nuls
        deficits_non_nuls = deficits_df[deficits_df['deficit'] != 0]
        deficits_positifs = deficits_df[deficits_df['deficit'] > 0]
        deficits_negatifs = deficits_df[deficits_df['deficit'] < 0]

        return {
            'total_deficits': len(deficits_non_nuls),
            'deficit_total': deficits_df['deficit'].sum(),
            'deficit_moyen': deficits_df['deficit'].mean(),
            'deficit_median': deficits_df['deficit'].median(),
            'magasins_concernes': deficits_non_nuls['magasin'].nunique(),
            'surplus_stock_count': len(deficits_positifs),
            'surplus_stock_total': deficits_positifs['deficit'].sum(),
            'manque_stock_count': len(deficits_negatifs),
            'manque_stock_total': abs(deficits_negatifs['deficit'].sum())
        }

    def get_top_deficits(self, analysis_result: AnalysisResult,
                        n: int = 10, by_abs_value: bool = True) -> pd.DataFrame:
        """
        Retourne les top déficits.

        Args:
            analysis_result: Résultat d'analyse des déficits
            n: Nombre de résultats à retourner
            by_abs_value: Trier par valeur absolue du déficit

        Returns:
            DataFrame des top déficits
        """
        df = analysis_result.data.copy()

        if by_abs_value:
            df['deficit_abs'] = abs(df['deficit'])
            result = df.nlargest(n, 'deficit_abs').drop('deficit_abs', axis=1)
        else:
            result = df.nlargest(n, 'deficit')

        return result.reset_index(drop=True)

    def get_magasin_summary(self, analysis_result: AnalysisResult) -> pd.DataFrame:
        """
        Retourne un résumé par magasin.

        Args:
            analysis_result: Résultat d'analyse des déficits

        Returns:
            DataFrame résumé par magasin
        """
        df = analysis_result.data

        summary = df.groupby('magasin').agg({
            'deficit': ['count', 'sum', 'mean'],
            'quantite_exploitation': 'sum',
            'quantite_stock': 'sum'
        }).round(2)

        # Aplatir les colonnes multi-niveaux
        summary.columns = ['nb_items', 'deficit_total', 'deficit_moyen',
                          'total_exploitation', 'total_stock']

        # Calculer le ratio exploitation/stock
        summary['ratio_exp_stock'] = (summary['total_exploitation'] /
                                     (summary['total_stock'] + 1)).round(3)

        return summary.sort_values('deficit_total', ascending=False).reset_index()

    def convert_to_deficit_items(self, analysis_result: AnalysisResult) -> List[DeficitItem]:
        """
        Convertit les résultats en objets DeficitItem.

        Args:
            analysis_result: Résultat d'analyse

        Returns:
            Liste d'objets DeficitItem
        """
        items = []
        for _, row in analysis_result.data.iterrows():
            item = DeficitItem(
                magasin=row['magasin'],
                nomenclature=row['nomenclature'],
                quantite_exploitation=row['quantite_exploitation'],
                quantite_stock=row['quantite_stock']
            )
            items.append(item)

        return items

    def clear_cache(self) -> None:
        """Vide le cache d'analyse."""
        self._cache.clear()
        logger.info("Cache d'analyse vidé")