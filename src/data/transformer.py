"""
Module de transformation des données d'inventaire.
"""
import pandas as pd
from typing import List
import logging

from ..core.exceptions import DataTransformationError
from ..core.models import InventoryItem


logger = logging.getLogger(__name__)


class InventoryTransformer:
    """Transformateur de données d'inventaire du format wide vers long."""

    def __init__(self):
        self._cache = {}

    def transform_to_long(self, df_wide: pd.DataFrame, use_cache: bool = True) -> pd.DataFrame:
        """
        Transforme les données du format wide (colonnes = magasins) vers le format long.

        Args:
            df_wide: DataFrame au format wide
            use_cache: Utiliser le cache pour éviter les recalculs

        Returns:
            DataFrame au format long

        Raises:
            DataTransformationError: Si la transformation échoue
        """
        if df_wide.empty:
            raise DataTransformationError("DataFrame vide fourni pour transformation")

        # Vérification du cache
        cache_key = f"transform_{hash(str(df_wide.values.tobytes()))}"
        if use_cache and cache_key in self._cache:
            logger.debug("Utilisation des données mises en cache")
            return self._cache[cache_key].copy()

        try:
            # Identifier la colonne de nomenclature (première colonne)
            nomenclature_col = df_wide.columns[0]
            logger.info(f"Colonne de nomenclature identifiée: {nomenclature_col}")

            # Transformer en format long
            df_long = pd.melt(
                df_wide,
                id_vars=[nomenclature_col],
                var_name='magasin_code',
                value_name='quantite'
            )

            # Nettoyer les données
            df_long = self._clean_data(df_long)

            # Extraire les informations de magasin
            df_long = self._extract_magasin_info(df_long)

            # Renommer la colonne de nomenclature pour cohérence
            df_long = df_long.rename(columns={nomenclature_col: 'nomenclature'})

            # Réorganiser les colonnes
            df_long = df_long[['nomenclature', 'magasin', 'magasin_code', 'type_donnee', 'quantite']]

            logger.info(f"Transformation terminée: {len(df_long)} entrées valides")

            # Mise en cache
            if use_cache:
                self._cache[cache_key] = df_long.copy()

            return df_long

        except Exception as e:
            raise DataTransformationError(f"Erreur lors de la transformation: {e}")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les données en supprimant les valeurs invalides.

        Args:
            df: DataFrame à nettoyer

        Returns:
            DataFrame nettoyé
        """
        initial_count = len(df)

        # Supprimer les valeurs nulles et vides
        df = df.dropna(subset=['quantite'])
        df = df[df['quantite'] != '']

        # Filtrer les codes de magasin valides (se terminant par -U ou -C)
        df = df[df['magasin_code'].str.match(r'.*-[UC]$', na=False)]

        # Convertir les quantités en numérique
        df['quantite'] = pd.to_numeric(df['quantite'], errors='coerce')

        # Supprimer les quantités non numériques et nulles/négatives
        df = df.dropna(subset=['quantite'])
        df = df[df['quantite'] > 0]

        cleaned_count = len(df)
        logger.debug(f"Nettoyage: {initial_count} -> {cleaned_count} entrées "
                    f"({initial_count - cleaned_count} supprimées)")

        return df

    def _extract_magasin_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrait les informations de magasin depuis le code de magasin.

        Args:
            df: DataFrame avec colonne magasin_code

        Returns:
            DataFrame avec colonnes magasin et type_donnee ajoutées
        """
        # Extraire le nom du magasin (supprimer le suffixe -U ou -C)
        df['magasin'] = df['magasin_code'].str.replace(r'-[UC]$', '', regex=True)

        # Extraire le type de donnée (U ou C)
        df['type_donnee'] = df['magasin_code'].str.extract(r'-([UC])$')[0]

        return df

    def convert_to_inventory_items(self, df_long: pd.DataFrame) -> List[InventoryItem]:
        """
        Convertit un DataFrame long en liste d'objets InventoryItem.

        Args:
            df_long: DataFrame au format long

        Returns:
            Liste d'objets InventoryItem
        """
        items = []
        for _, row in df_long.iterrows():
            item = InventoryItem(
                nomenclature=row['nomenclature'],
                magasin=row['magasin'],
                type_donnee=row['type_donnee'],
                quantite=row['quantite']
            )
            items.append(item)

        logger.info(f"Conversion terminée: {len(items)} objets InventoryItem créés")
        return items

    def filter_by_magasin(self, df_long: pd.DataFrame, magasin: str) -> pd.DataFrame:
        """
        Filtre les données pour un magasin spécifique.

        Args:
            df_long: DataFrame au format long
            magasin: Nom du magasin

        Returns:
            DataFrame filtré
        """
        result = df_long[df_long['magasin'] == magasin].copy()
        logger.info(f"Filtrage magasin '{magasin}': {len(result)} entrées trouvées")
        return result

    def filter_by_nomenclature(self, df_long: pd.DataFrame, nomenclature: str) -> pd.DataFrame:
        """
        Filtre les données pour une nomenclature spécifique.

        Args:
            df_long: DataFrame au format long
            nomenclature: Code de nomenclature

        Returns:
            DataFrame filtré
        """
        result = df_long[df_long['nomenclature'] == nomenclature].copy()
        logger.info(f"Filtrage nomenclature '{nomenclature}': {len(result)} entrées trouvées")
        return result

    def clear_cache(self) -> None:
        """Vide le cache de transformation."""
        self._cache.clear()
        logger.info("Cache de transformation vidé")