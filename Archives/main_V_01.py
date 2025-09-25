import pandas as pd
from typing import Optional

class DeficitAnalyzer:
    def __init__(self, dataframe: pd.DataFrame):
        if dataframe is None:
            raise ValueError("DataFrame cannot be None")

        if dataframe.empty:
            raise ValueError("DataFrame cannot be empty")

        self.df = self._transform_data(dataframe)

    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform wide format CSV to long format for analysis."""
        # Get nomenclature column (first column)
        nomenclature_col = df.columns[0]

        # Melt the dataframe to long format
        df_long = pd.melt(df,
                         id_vars=[nomenclature_col],
                         var_name='magasin_code',
                         value_name='quantite')

        # Remove empty values and filter valid store codes
        df_long = df_long.dropna(subset=['quantite'])
        df_long = df_long[df_long['quantite'] != '']
        df_long = df_long[df_long['magasin_code'].str.match(r'.*-[UC]$', na=False)]

        # Convert quantities to numeric
        df_long['quantite'] = pd.to_numeric(df_long['quantite'], errors='coerce')
        df_long = df_long.dropna(subset=['quantite'])
        df_long = df_long[df_long['quantite'] > 0]

        # Rename columns for consistency
        df_long = df_long.rename(columns={
            nomenclature_col: 'nomenclature',
            'magasin_code': 'code'
        })

        # Extract magasin name (remove -U or -C suffix)
        df_long['magasin'] = df_long['code'].str.replace(r'-[UC]$', '', regex=True)

        return df_long

    def analyze_deficits(self) -> pd.DataFrame:
        """Analyze deficits between exploitation (-U) and stock (-C) data."""
        # Split exploitation and stock data
        exploitation = self.df[self.df['code'].str.endswith('-U')].copy()
        stock = self.df[self.df['code'].str.endswith('-C')].copy()

        if exploitation.empty or stock.empty:
            return pd.DataFrame(columns=['magasin', 'nomenclature', 'quantite_exploitation', 'quantite_stock', 'deficit'])

        # Merge data on magasin and nomenclature
        deficits = exploitation.merge(
            stock,
            on=['magasin', 'nomenclature'],
            suffixes=('_exploitation', '_stock'),
            how='outer'
        )

        # Handle missing values
        deficits['quantite_exploitation'] = deficits['quantite_exploitation'].fillna(0)
        deficits['quantite_stock'] = deficits['quantite_stock'].fillna(0)

        # Calculate deficit
        deficits['deficit'] = deficits['quantite_exploitation'] - deficits['quantite_stock']

        # Keep only columns we need
        result = deficits[['magasin', 'nomenclature', 'quantite_exploitation', 'quantite_stock', 'deficit']].copy()

        # Sort by magasin and nomenclature
        return result.sort_values(['magasin', 'nomenclature']).reset_index(drop=True)


def import_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    Importe un fichier CSV dans une dataframe Pandas.

    Args:
        file_path: Chemin d'accès au fichier CSV.

    Returns:
        DataFrame contenant les données ou None si erreur.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        pd.errors.ParserError: Si le fichier ne peut pas être analysé.
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if df.empty:
            print(f"Attention : Le fichier {file_path} est vide.")
            return None

        print(f"Fichier CSV importé avec succès : {file_path} ({len(df)} lignes)")
        return df

    except FileNotFoundError as e:
        print(f"Erreur : Le fichier {file_path} n'a pas été trouvé.")
        raise e
    except pd.errors.ParserError as e:
        print(f"Erreur : Impossible d'analyser le fichier {file_path}.")
        raise e
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
            print(f"Fichier CSV importé avec encodage latin-1 : {file_path} ({len(df)} lignes)")
            return df
        except Exception as e:
            print(f"Erreur d'encodage pour le fichier {file_path} : {e}")
            raise e
    except Exception as e:
        print(f"Erreur inattendue lors de l'importation du fichier {file_path} : {e}")
        raise e
    
def main() -> None:
    """Fonction principale du programme."""
    try:
        df = import_csv('./data/inventaire_court.csv')
        if df is None:
            print("Impossible de continuer : fichier CSV invalide.")
            return

        analyzer = DeficitAnalyzer(df)
        resultats = analyzer.analyze_deficits()

        if resultats.empty:
            print("Aucun déficit détecté.")
        else:
            print(f"\n{len(resultats)} déficits détectés :")
            print("=" * 50)
            print(resultats.to_string(index=False))

            print(f"\nRésumé :")
            print(f"- Nombre de magasins concernés : {resultats['magasin'].nunique()}")
            print(f"- Déficit total : {resultats['deficit'].sum()}")
            print(f"- Déficit moyen : {resultats['deficit'].mean():.2f}")

    except ValueError as e:
        print(f"Erreur de validation : {e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")


if __name__ == "__main__":
    main()
