"""
Module de visualisation des données d'inventaire.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Optional, Tuple
import logging

from ..core.exceptions import VisualizationError
from ..core.models import AnalysisResult


logger = logging.getLogger(__name__)


class InventoryCharts:
    """Générateur de graphiques pour les données d'inventaire."""

    def __init__(self, style: str = 'seaborn-v0_8', figsize: Tuple[int, int] = (12, 8)):
        """
        Initialise le générateur de graphiques.

        Args:
            style: Style matplotlib à utiliser
            figsize: Taille par défaut des figures
        """
        self.figsize = figsize
        try:
            plt.style.use(style)
        except OSError:
            logger.warning(f"Style {style} non disponible, utilisation du style par défaut")
            plt.style.use('default')

        # Configuration seaborn
        sns.set_palette("husl")

    def plot_top_magasins(self, analysis_result: AnalysisResult,
                          title: str = "Top Magasins par Quantité",
                          save_path: Optional[str] = None) -> None:
        """
        Crée un graphique en barres des top magasins.

        Args:
            analysis_result: Résultat d'analyse contenant les données
            title: Titre du graphique
            save_path: Chemin pour sauvegarder le graphique

        Raises:
            VisualizationError: Si la création du graphique échoue
        """
        try:
            df = analysis_result.data
            if df.empty:
                raise VisualizationError("Aucune donnée à visualiser")

            plt.figure(figsize=self.figsize)

            # Créer le graphique en barres
            bars = plt.bar(range(len(df)), df['quantite'], color='steelblue', alpha=0.8)

            # Personnaliser le graphique
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Magasin', fontsize=12)
            plt.ylabel('Quantité Totale', fontsize=12)

            # Configurer les labels de l'axe x
            plt.xticks(range(len(df)), df['magasin'], rotation=45, ha='right')

            # Ajouter les valeurs sur les barres
            for i, (bar, value) in enumerate(zip(bars, df['quantite'])):
                plt.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + value * 0.01,
                        f'{value:.0f}',
                        ha='center', va='bottom', fontsize=9)

            # Ajouter une grille
            plt.grid(axis='y', alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Graphique sauvegardé: {save_path}")

            plt.show()

        except Exception as e:
            raise VisualizationError(f"Erreur lors de la création du graphique des magasins: {e}")

    def plot_top_nomenclatures(self, analysis_result: AnalysisResult,
                             title: str = "Top Nomenclatures par Quantité",
                             save_path: Optional[str] = None) -> None:
        """
        Crée un graphique en barres des top nomenclatures.

        Args:
            analysis_result: Résultat d'analyse
            title: Titre du graphique
            save_path: Chemin pour sauvegarder

        Raises:
            VisualizationError: Si la création échoue
        """
        try:
            df = analysis_result.data
            if df.empty:
                raise VisualizationError("Aucune donnée à visualiser")

            plt.figure(figsize=self.figsize)

            # Graphique horizontal pour les nomenclatures (souvent de longs codes)
            bars = plt.barh(range(len(df)), df['quantite'], color='coral', alpha=0.8)

            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Quantité Totale', fontsize=12)
            plt.ylabel('Nomenclature', fontsize=12)

            # Inverser l'ordre pour avoir le plus grand en haut
            plt.yticks(range(len(df)), df['nomenclature'])
            plt.gca().invert_yaxis()

            # Ajouter les valeurs
            for i, (bar, value) in enumerate(zip(bars, df['quantite'])):
                plt.text(bar.get_width() + value * 0.01,
                        bar.get_y() + bar.get_height()/2,
                        f'{value:.0f}',
                        ha='left', va='center', fontsize=9)

            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Graphique sauvegardé: {save_path}")

            plt.show()

        except Exception as e:
            raise VisualizationError(f"Erreur lors de la création du graphique des nomenclatures: {e}")

    def plot_distribution(self, df_long: pd.DataFrame,
                         title: str = "Distribution des Quantités",
                         save_path: Optional[str] = None) -> None:
        """
        Crée un graphique de distribution des quantités.

        Args:
            df_long: DataFrame au format long
            title: Titre du graphique
            save_path: Chemin pour sauvegarder

        Raises:
            VisualizationError: Si la création échoue
        """
        try:
            if df_long.empty:
                raise VisualizationError("Aucune donnée à visualiser")

            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(title, fontsize=16, fontweight='bold')

            # Histogramme
            axes[0, 0].hist(df_long['quantite'], bins=50, alpha=0.7,
                           color='skyblue', edgecolor='black')
            axes[0, 0].set_title('Histogramme des Quantités')
            axes[0, 0].set_xlabel('Quantité')
            axes[0, 0].set_ylabel('Fréquence')
            axes[0, 0].set_yscale('log')
            axes[0, 0].grid(True, alpha=0.3)

            # Box plot
            axes[0, 1].boxplot(df_long['quantite'])
            axes[0, 1].set_title('Box Plot des Quantités')
            axes[0, 1].set_ylabel('Quantité')
            axes[0, 1].set_yscale('log')
            axes[0, 1].grid(True, alpha=0.3)

            # Distribution par type (U vs C)
            if 'type_donnee' in df_long.columns:
                for type_donnee in df_long['type_donnee'].unique():
                    data = df_long[df_long['type_donnee'] == type_donnee]['quantite']
                    axes[1, 0].hist(data, alpha=0.6, label=f'Type {type_donnee}',
                                   bins=30, density=True)

                axes[1, 0].set_title('Distribution par Type (U vs C)')
                axes[1, 0].set_xlabel('Quantité')
                axes[1, 0].set_ylabel('Densité')
                axes[1, 0].legend()
                axes[1, 0].grid(True, alpha=0.3)

            # Q-Q plot pour normalité
            from scipy import stats
            stats.probplot(df_long['quantite'], dist="norm", plot=axes[1, 1])
            axes[1, 1].set_title('Q-Q Plot (Test de Normalité)')
            axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Graphique sauvegardé: {save_path}")

            plt.show()

        except Exception as e:
            raise VisualizationError(f"Erreur lors de la création du graphique de distribution: {e}")

    def plot_exploitation_vs_stock(self, analysis_result: AnalysisResult,
                                  title: str = "Comparaison Exploitation vs Stock",
                                  save_path: Optional[str] = None) -> None:
        """
        Crée un graphique comparant exploitation et stock par magasin.

        Args:
            analysis_result: Résultat d'analyse
            title: Titre du graphique
            save_path: Chemin pour sauvegarder

        Raises:
            VisualizationError: Si la création échoue
        """
        try:
            df = analysis_result.data
            if df.empty:
                raise VisualizationError("Aucune donnée à visualiser")

            fig, axes = plt.subplots(2, 1, figsize=(15, 12))
            fig.suptitle(title, fontsize=16, fontweight='bold')

            # Graphique en barres groupées
            x = range(len(df))
            width = 0.35

            bars1 = axes[0].bar([i - width/2 for i in x], df['U'],
                              width, label='Exploitation (U)', color='orange', alpha=0.7)
            bars2 = axes[0].bar([i + width/2 for i in x], df['C'],
                              width, label='Stock (C)', color='green', alpha=0.7)

            axes[0].set_xlabel('Magasin')
            axes[0].set_ylabel('Quantité Totale')
            axes[0].set_title('Comparaison des Quantités par Magasin')
            axes[0].set_xticks(x)
            axes[0].set_xticklabels(df['magasin'], rotation=45, ha='right')
            axes[0].legend()
            axes[0].grid(axis='y', alpha=0.3)

            # Graphique des ratios
            ratios = df['ratio_U_C']
            colors = ['red' if r > 1.1 else 'orange' if r > 0.9 else 'green' for r in ratios]

            bars3 = axes[1].bar(x, ratios, color=colors, alpha=0.7)
            axes[1].set_xlabel('Magasin')
            axes[1].set_ylabel('Ratio Exploitation/Stock')
            axes[1].set_title('Ratio Exploitation/Stock par Magasin')
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(df['magasin'], rotation=45, ha='right')
            axes[1].axhline(y=1, color='black', linestyle='--', alpha=0.5, label='Équilibre')
            axes[1].legend()
            axes[1].grid(axis='y', alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Graphique sauvegardé: {save_path}")

            plt.show()

        except Exception as e:
            raise VisualizationError(f"Erreur lors de la création du graphique de comparaison: {e}")

    def plot_deficit_heatmap(self, analysis_result: AnalysisResult,
                           title: str = "Heatmap des Déficits par Magasin",
                           save_path: Optional[str] = None) -> None:
        """
        Crée une heatmap des déficits.

        Args:
            analysis_result: Résultat d'analyse des déficits
            title: Titre du graphique
            save_path: Chemin pour sauvegarder

        Raises:
            VisualizationError: Si la création échoue
        """
        try:
            df = analysis_result.data
            if df.empty:
                raise VisualizationError("Aucune donnée à visualiser")

            # Créer une matrice pivot pour la heatmap
            # Limitation aux top nomenclatures pour la lisibilité
            top_nomenclatures = (df.groupby('nomenclature')['deficit']
                               .apply(lambda x: abs(x).sum())
                               .nlargest(20)
                               .index.tolist())

            df_filtered = df[df['nomenclature'].isin(top_nomenclatures)]

            pivot_df = df_filtered.pivot(index='nomenclature',
                                       columns='magasin',
                                       values='deficit')

            plt.figure(figsize=(16, 10))

            # Créer la heatmap
            sns.heatmap(pivot_df,
                       center=0,
                       cmap='RdBu_r',
                       annot=False,
                       fmt='.0f',
                       cbar_kws={'label': 'Déficit (Exploitation - Stock)'},
                       xticklabels=True,
                       yticklabels=True)

            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Magasin', fontsize=12)
            plt.ylabel('Nomenclature', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Heatmap sauvegardée: {save_path}")

            plt.show()

        except Exception as e:
            raise VisualizationError(f"Erreur lors de la création de la heatmap: {e}")

    def close_all(self) -> None:
        """Ferme toutes les figures ouvertes."""
        plt.close('all')
        logger.info("Toutes les figures fermées")