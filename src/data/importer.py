"""
Module d'importation des données d'inventaire.
"""
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from ..core.exceptions import DataImportError, DataValidationError


logger = logging.getLogger(__name__)


class InventoryImporter:
    """Gestionnaire d'importation des fichiers d'inventaire."""

    def __init__(self):
        self._supported_encodings = ['utf-8', 'latin-1', 'cp1252']

    def import_csv(self, file_path: str) -> pd.DataFrame:
        """
        Importe un fichier CSV d'inventaire.

        Args:
            file_path: Chemin vers le fichier CSV

        Returns:
            DataFrame contenant les données brutes

        Raises:
            DataImportError: Si l'importation échoue
            DataValidationError: Si les données ne sont pas valides
        """
        path = Path(file_path)

        if not path.exists():
            raise DataImportError(f"Le fichier {file_path} n'existe pas")

        if not path.suffix.lower() == '.csv':
            raise DataImportError(f"Format de fichier non supporté: {path.suffix}")

        # Tentative d'importation avec différents encodages
        last_error = None
        for encoding in self._supported_encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Fichier importé avec succès avec l'encodage {encoding}: "
                           f"{file_path} ({len(df)} lignes, {len(df.columns)} colonnes)")

                self._validate_data(df, file_path)
                return df

            except UnicodeDecodeError as e:
                last_error = e
                logger.debug(f"Échec avec l'encodage {encoding}: {e}")
                continue
            except Exception as e:
                raise DataImportError(f"Erreur lors de l'analyse du fichier {file_path}: {e}")

        raise DataImportError(
            f"Impossible de lire le fichier {file_path} avec les encodages supportés. "
            f"Dernière erreur: {last_error}"
        )

    def _validate_data(self, df: pd.DataFrame, file_path: str) -> None:
        """
        Valide les données importées.

        Args:
            df: DataFrame à valider
            file_path: Chemin du fichier pour les messages d'erreur

        Raises:
            DataValidationError: Si les données ne sont pas valides
        """
        if df.empty:
            raise DataValidationError(f"Le fichier {file_path} est vide")

        if len(df.columns) < 2:
            raise DataValidationError(
                f"Le fichier {file_path} doit contenir au moins 2 colonnes "
                f"(nomenclature + magasins), trouvé: {len(df.columns)}"
            )

        # Vérifier qu'il y a des colonnes avec les suffixes -U ou -C
        magasin_cols = [col for col in df.columns[1:] if isinstance(col, str) and col.endswith(('-U', '-C'))]
        if not magasin_cols:
            raise DataValidationError(
                f"Aucune colonne de magasin trouvée avec les suffixes -U ou -C dans {file_path}"
            )

        logger.info(f"Validation réussie: {len(magasin_cols)} colonnes de magasins détectées")

    def get_file_info(self, file_path: str) -> dict:
        """
        Retourne des informations sur le fichier sans l'importer complètement.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Dictionnaire contenant les informations du fichier
        """
        try:
            # Lecture des premières lignes seulement
            df_sample = pd.read_csv(file_path, nrows=5)

            return {
                'path': file_path,
                'exists': Path(file_path).exists(),
                'size_bytes': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                'estimated_columns': len(df_sample.columns),
                'estimated_magasin_columns': len([col for col in df_sample.columns[1:]
                                                 if isinstance(col, str) and col.endswith(('-U', '-C'))]),
                'sample_data': df_sample.head(3).to_dict()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention des informations du fichier {file_path}: {e}")
            return {
                'path': file_path,
                'exists': Path(file_path).exists(),
                'error': str(e)
            }