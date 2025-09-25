import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Dict, Union
import numpy as np
import warnings

warnings.filterwarnings("ignore")


class AnalyseurInventaire:
    def __init__(self, chemin_fichier: str):
        """
        Analyseur spécialisé pour les données d'inventaire au format wide.

        Args:
            chemin_fichier: Chemin vers le fichier CSV d'inventaire
        """
        try:
            self.df_raw = pd.read_csv(chemin_fichier, encoding="utf-8")
            print(
                f"Fichier importé avec succès: {chemin_fichier} ({len(self.df_raw)} lignes)"
            )
        except UnicodeDecodeError:
            self.df_raw = pd.read_csv(chemin_fichier, encoding="latin-1")
            print(
                f"Fichier importé avec encodage latin-1: {chemin_fichier} ({len(self.df_raw)} lignes)"
            )
        except Exception as e:
            raise ValueError(f"Impossible de lire le fichier {chemin_fichier}: {e}")

        self.nomenclature_col = self.df_raw.columns[0]
        self.df_long = self._transformer_donnees()

    def _transformer_donnees(self) -> pd.DataFrame:
        """Transforme les données du format wide vers le format long."""
        df_long = pd.melt(
            self.df_raw,
            id_vars=[self.nomenclature_col],
            var_name="magasin_code",
            value_name="quantite",
        )

        # Nettoyer les données
        df_long = df_long.dropna(subset=["quantite"])
        df_long = df_long[df_long["quantite"] != ""]
        df_long = df_long[df_long["magasin_code"].str.match(r".*-[UC]$", na=False)]

        # Convertir en numérique
        df_long["quantite"] = pd.to_numeric(df_long["quantite"], errors="coerce")
        df_long = df_long.dropna(subset=["quantite"])
        df_long = df_long[df_long["quantite"] > 0]

        # Extraire le nom du magasin
        df_long["magasin"] = df_long["magasin_code"].str.replace(
            r"-[UC]$", "", regex=True
        )
        df_long["type"] = df_long["magasin_code"].str.extract(r"-([UC])$")[0]

        return df_long.rename(columns={self.nomenclature_col: "nomenclature"})

    def afficher_apercu(self, n: int = 5) -> None:
        """Affiche un aperçu des données."""
        print("\n=== APERÇU DES DONNÉES BRUTES ===")
        print(f"Dimensions: {self.df_raw.shape}")
        print(
            f"Colonnes: {list(self.df_raw.columns[:10])}{'...' if len(self.df_raw.columns) > 10 else ''}"
        )
        print("\nPremières lignes:")
        print(self.df_raw.head(n))

        print("\n=== DONNÉES TRANSFORMÉES ===")
        print(f"Dimensions: {self.df_long.shape}")
        print(self.df_long.head(n))

    def statistiques_globales(self) -> Dict[str, Union[int, float]]:
        """Retourne des statistiques globales sur l'inventaire."""
        stats = {
            "nombre_nomenclatures": self.df_long["nomenclature"].nunique(),
            "nombre_magasins": self.df_long["magasin"].nunique(),
            "nombre_total_entrees": len(self.df_long),
            "quantite_totale": self.df_long["quantite"].sum(),
            "quantite_moyenne": self.df_long["quantite"].mean(),
            "quantite_mediane": self.df_long["quantite"].median(),
            "quantite_max": self.df_long["quantite"].max(),
            "quantite_min": self.df_long["quantite"].min(),
        }

        print("\n=== STATISTIQUES GLOBALES ===")
        for cle, valeur in stats.items():
            if isinstance(valeur, float):
                print(f"{cle.replace('_', ' ').title()}: {valeur:.2f}")
            else:
                print(f"{cle.replace('_', ' ').title()}: {valeur:,}")

        return stats

    def top_nomenclatures(self, n: int = 10) -> pd.DataFrame:
        """Retourne les n nomenclatures avec les plus grandes quantités."""
        top = (
            self.df_long.groupby("nomenclature")["quantite"]
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )

        print(f"\n=== TOP {n} NOMENCLATURES (par quantité totale) ===")
        print(top.to_string(index=False))
        return top

    def top_magasins(self, n: int = 10) -> pd.DataFrame:
        """Retourne les n magasins avec les plus grandes quantités."""
        top = (
            self.df_long.groupby("magasin")["quantite"]
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )

        print(f"\n=== TOP {n} MAGASINS (par quantité totale) ===")
        print(top.to_string(index=False))
        return top

    def analyser_deficits(self) -> pd.DataFrame:
        """Analyse les déficits entre exploitation (U) et stock (C)."""
        exploitation = self.df_long[self.df_long["type"] == "U"].copy()
        stock = self.df_long[self.df_long["type"] == "C"].copy()

        if exploitation.empty or stock.empty:
            print("Données insuffisantes pour analyser les déficits")
            return pd.DataFrame()

        deficits = exploitation.merge(
            stock,
            on=["magasin", "nomenclature"],
            suffixes=("_exploitation", "_stock"),
            how="outer",
        )

        deficits["quantite_exploitation"] = deficits["quantite_exploitation"].fillna(0)
        deficits["quantite_stock"] = deficits["quantite_stock"].fillna(0)
        deficits["deficit"] = (
            deficits["quantite_exploitation"] - deficits["quantite_stock"]
        )

        result = deficits[deficits["deficit"] != 0][
            [
                "magasin",
                "nomenclature",
                "quantite_exploitation",
                "quantite_stock",
                "deficit",
            ]
        ].copy()

        print(f"\n=== ANALYSE DES DÉFICITS ===")
        print(f"Nombre total de déficits: {len(result):,}")
        if not result.empty:
            print(f"Déficit total: {result['deficit'].sum():.0f}")
            print(f"Déficit moyen: {result['deficit'].mean():.2f}")
            print(f"Magasins concernés: {result['magasin'].nunique()}")

        return result.sort_values(["magasin", "nomenclature"]).reset_index(drop=True)

    def filtrer_par_magasin(self, magasin: str) -> pd.DataFrame:
        """Filtre les données pour un magasin spécifique."""
        result = self.df_long[self.df_long["magasin"] == magasin].copy()
        print(f"\n=== DONNÉES POUR LE MAGASIN: {magasin} ===")
        print(f"Nombre d'entrées: {len(result)}")
        print(f"Quantité totale: {result['quantite'].sum():.0f}")
        return result

    def filtrer_par_nomenclature(self, nomenclature: str) -> pd.DataFrame:
        """Filtre les données pour une nomenclature spécifique."""
        result = self.df_long[self.df_long["nomenclature"] == nomenclature].copy()
        print(f"\n=== DONNÉES POUR LA NOMENCLATURE: {nomenclature} ===")
        print(f"Nombre d'entrées: {len(result)}")
        print(f"Quantité totale: {result['quantite'].sum():.0f}")
        return result

    def visualiser_top_magasins(self, n: int = 15) -> None:
        """Visualise les top magasins par quantité."""
        top_data = (
            self.df_long.groupby("magasin")["quantite"]
            .sum()
            .sort_values(ascending=False)
            .head(n)
        )

        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(top_data)), top_data.values, color="steelblue")
        plt.xticks(range(len(top_data)), top_data.index, rotation=45, ha="right")
        plt.title(f"Top {n} Magasins par Quantité Totale")
        plt.xlabel("Magasin")
        plt.ylabel("Quantité Totale")
        plt.grid(axis="y", alpha=0.3)

        # Ajouter les valeurs sur les barres
        for bar, value in zip(bars, top_data.values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + value * 0.01,
                f"{value:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        plt.show()

    def visualiser_distribution_quantites(self) -> None:
        """Visualise la distribution des quantités."""
        plt.figure(figsize=(12, 6))

        # Histogramme avec échelle log pour mieux voir la distribution
        plt.subplot(1, 2, 1)
        plt.hist(
            self.df_long["quantite"],
            bins=50,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
        )
        plt.title("Distribution des Quantités")
        plt.xlabel("Quantité")
        plt.ylabel("Fréquence")
        plt.yscale("log")
        plt.grid(True, alpha=0.3)

        # Box plot
        plt.subplot(1, 2, 2)
        plt.boxplot(self.df_long["quantite"], vert=True)
        plt.title("Box Plot des Quantités")
        plt.ylabel("Quantité")
        plt.yscale("log")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def comparer_exploitation_stock(self) -> None:
        """Compare les quantités entre exploitation (U) et stock (C)."""
        if "type" not in self.df_long.columns:
            print("Impossible de comparer - types non disponibles")
            return

        comparison = (
            self.df_long.groupby(["magasin", "type"])["quantite"]
            .sum()
            .unstack(fill_value=0)
        )

        if "U" in comparison.columns and "C" in comparison.columns:
            plt.figure(figsize=(12, 8))

            plt.subplot(2, 1, 1)
            x = range(len(comparison.index))
            width = 0.35

            plt.bar(
                [i - width / 2 for i in x],
                comparison["U"],
                width,
                label="Exploitation (U)",
                color="orange",
                alpha=0.7,
            )
            plt.bar(
                [i + width / 2 for i in x],
                comparison["C"],
                width,
                label="Stock (C)",
                color="green",
                alpha=0.7,
            )

            plt.xlabel("Magasin")
            plt.ylabel("Quantité Totale")
            plt.title("Comparaison Exploitation vs Stock par Magasin")
            plt.xticks(x, comparison.index, rotation=45, ha="right")
            plt.legend()
            plt.grid(axis="y", alpha=0.3)

            # Ratio exploitation/stock
            plt.subplot(2, 1, 2)
            ratio = comparison["U"] / (
                comparison["C"] + 1
            )  # +1 pour éviter division par 0
            colors = [
                "red" if r > 1.1 else "orange" if r > 0.9 else "green" for r in ratio
            ]
            plt.bar(x, ratio, color=colors, alpha=0.7)
            plt.xlabel("Magasin")
            plt.ylabel("Ratio Exploitation/Stock")
            plt.title("Ratio Exploitation/Stock par Magasin")
            plt.xticks(x, comparison.index, rotation=45, ha="right")
            plt.axhline(y=1, color="black", linestyle="--", alpha=0.5)
            plt.grid(axis="y", alpha=0.3)

            plt.tight_layout()
            plt.show()

    def exporter_donnees(
        self, chemin_export: str, donnees: str = "long", format: str = "csv"
    ) -> None:
        """
        Exporte les données dans le format spécifié.

        Args:
            chemin_export: Chemin de destination
            donnees: 'raw', 'long', ou 'deficits'
            format: 'csv' ou 'excel'
        """
        if donnees == "raw":
            data_to_export = self.df_raw
        elif donnees == "long":
            data_to_export = self.df_long
        elif donnees == "deficits":
            data_to_export = self.analyser_deficits()
        else:
            raise ValueError("donnees doit être 'raw', 'long', ou 'deficits'")

        try:
            if format == "csv":
                data_to_export.to_csv(chemin_export, index=False, encoding="utf-8")
                print(f"Données exportées au format CSV : {chemin_export}")
            elif format == "excel":
                data_to_export.to_excel(chemin_export, index=False)
                print(f"Données exportées au format Excel : {chemin_export}")
            else:
                raise ValueError("Format non supporté. Utilisez 'csv' ou 'excel'.")
        except Exception as e:
            print(f"Erreur lors de l'export : {e}")


def main() -> None:
    """Fonction principale de démonstration."""
    try:
        # Initialiser l'analyseur
        chemin_fichier = "./data/inventaire_court.csv"
        analyseur = AnalyseurInventaire(chemin_fichier)

        # Afficher un aperçu des données
        analyseur.afficher_apercu(3)

        # Statistiques globales
        stats = analyseur.statistiques_globales()

        # Top analyses
        analyseur.top_magasins(15)
        analyseur.top_nomenclatures(10)

        # Analyse des déficits
        deficits = analyseur.analyser_deficits()

        # Exemples de filtrage
        if len(analyseur.df_long) > 0:
            # Prendre le premier magasin comme exemple
            premier_magasin = analyseur.df_long["magasin"].iloc[0]
            analyseur.filtrer_par_magasin(premier_magasin)

            # Prendre la première nomenclature comme exemple
            premiere_nomenclature = analyseur.df_long["nomenclature"].iloc[0]
            analyseur.filtrer_par_nomenclature(premiere_nomenclature)

        print("\n=== FONCTIONNALITÉS DISPONIBLES ===")
        print("- analyseur.visualiser_top_magasins()")
        print("- analyseur.visualiser_distribution_quantites()")
        print("- analyseur.comparer_exploitation_stock()")
        print("- analyseur.exporter_donnees('export.csv', 'deficits')")

    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")


if __name__ == "__main__":
    main()
