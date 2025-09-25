import pandas as pd
import streamlit as st
from typing import Union
import io

def importer_fichier(fichier: Union[str, st.runtime.uploaded_file_manager.UploadedFile]) -> pd.DataFrame:
    """
    Importe un fichier CSV ou Excel depuis un chemin ou un objet UploadedFile de Streamlit.

    Args:
        fichier: Chemin du fichier (str) ou objet UploadedFile de Streamlit

    Returns:
        DataFrame pandas contenant les données du fichier

    Raises:
        ValueError: Si le format de fichier n'est pas supporté
        Exception: Pour les erreurs de lecture de fichier
    """
    try:
        # Si c'est un objet UploadedFile de Streamlit
        if hasattr(fichier, 'name'):
            if fichier.name.endswith('.csv'):
                return pd.read_csv(fichier, encoding='utf-8')
            elif fichier.name.endswith('.xlsx'):
                return pd.read_excel(fichier, engine='openpyxl')
            else:
                raise ValueError(f"Format non supporté: {fichier.name}. Utilise .csv ou .xlsx")

        # Si c'est un chemin de fichier (str)
        elif isinstance(fichier, str):
            if fichier.endswith('.csv'):
                return pd.read_csv(fichier, encoding='utf-8')
            elif fichier.endswith('.xlsx'):
                return pd.read_excel(fichier, engine='openpyxl')
            else:
                raise ValueError(f"Format non supporté: {fichier}. Utilise .csv ou .xlsx")

        else:
            raise ValueError("Type de fichier non reconnu")

    except Exception as e:
        raise Exception(f"Erreur lors de la lecture du fichier: {str(e)}")

def valider_colonnes(df: pd.DataFrame, colonnes_requises: list = ['Magasin', 'Matériel', 'Stock']) -> bool:
    """
    Valide que le DataFrame contient les colonnes requises.

    Args:
        df: DataFrame à valider
        colonnes_requises: Liste des colonnes qui doivent être présentes

    Returns:
        bool: True si toutes les colonnes sont présentes

    Raises:
        ValueError: Si des colonnes sont manquantes
    """
    colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
    if colonnes_manquantes:
        raise ValueError(f"Colonnes manquantes dans le fichier: {', '.join(colonnes_manquantes)}. Colonnes requises: {', '.join(colonnes_requises)}")
    return True
