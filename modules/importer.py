import pandas as pd

def importer_fichier(path: str) -> pd.DataFrame:
    if path.endswith('.csv'):
        return pd.read_csv(path)
    elif path.endswith('.xlsx'):
        return pd.read_excel(path, engine='openpyxl')
    else:
        raise ValueError("Format non supporté. Utilise .csv ou .xlsx")
