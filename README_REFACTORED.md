# Material Manager - Version Refactorisée

## 🎯 Vue d'ensemble

Cette version refactorisée améliore significativement l'architecture du gestionnaire de matériel, en appliquant les principes SOLID et en séparant les responsabilités en modules spécialisés.

## 🏗️ Architecture

### Structure des répertoires

```
├── src/                          # Code source principal
│   ├── core/                     # Composants centraux
│   │   ├── exceptions.py         # Exceptions personnalisées
│   │   ├── models.py             # Modèles de données
│   │   └── manager.py            # Gestionnaire principal
│   ├── data/                     # Gestion des données
│   │   ├── importer.py           # Import des fichiers CSV
│   │   └── transformer.py        # Transformation wide → long
│   ├── analysis/                 # Analyses spécialisées
│   │   ├── deficit_analyzer.py   # Analyse des déficits U/C
│   │   └── stats_analyzer.py     # Statistiques générales
│   └── visualization/            # Génération de graphiques
│       └── charts.py             # Graphiques matplotlib/seaborn
├── tests/                        # Tests unitaires
├── main_refactored.py            # Interface principale
├── test_simple.py                # Tests rapides
└── requirements.txt              # Dépendances
```

## 🚀 Utilisation rapide

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Analyse complète

```python
python main_refactored.py
```

### Utilisation programmatique

```python
from src.core.manager import MaterialManager

# Initialisation
manager = MaterialManager()

# Chargement des données
manager.load_data('./data/inventaire_court.csv')

# Analyses
stats = manager.calculate_global_statistics()
deficits = manager.analyze_deficits()
top_magasins = manager.get_top_magasins(10)

# Exports
manager.export_data('deficits.csv', 'deficits')
manager.generate_visualizations('output/')
```

## 📊 Fonctionnalités principales

### 1. Analyse des déficits U/C
- **Exploitation (U)** : Quantités utilisées en réalité
- **Stock (C)** : Quantités théoriques en stock
- **Déficit** : Différence entre exploitation et stock

### 2. Statistiques avancées
- Statistiques globales (moyenne, médiane, etc.)
- Top magasins et nomenclatures
- Distribution des quantités
- Comparaison exploitation vs stock

### 3. Visualisations
- Graphiques en barres des top magasins/nomenclatures
- Histogrammes et box plots de distribution
- Heatmaps des déficits
- Comparaisons exploitation vs stock

### 4. Export et filtrage
- Export CSV/Excel des données et résultats
- Filtrage par magasin ou nomenclature
- Cache intelligent pour les performances

## 🔧 Améliorations apportées

### Architecture
- ✅ **Séparation des responsabilités** : Chaque module a une fonction précise
- ✅ **Exceptions personnalisées** : Gestion d'erreurs robuste
- ✅ **Modèles de données** : Types structurés avec dataclasses
- ✅ **Cache intelligent** : Évite les recalculs coûteux
- ✅ **Logging structuré** : Traçabilité des opérations

### Code Quality
- ✅ **DRY (Don't Repeat Yourself)** : Élimination de la duplication
- ✅ **SOLID principles** : Classes avec responsabilités uniques
- ✅ **Type hints** : Documentation des types
- ✅ **Docstrings** : Documentation complète
- ✅ **Tests unitaires** : Validation du comportement

### Performance
- ✅ **Transformations optimisées** : Pandas efficace
- ✅ **Cache des résultats** : Évite les recalculs
- ✅ **Gestion mémoire** : Nettoyage des données inutiles
- ✅ **Import intelligent** : Encodages multiples supportés

## 📈 Résultats d'analyse

L'analyse du fichier `inventaire_court.csv` révèle :

### Statistiques globales
- **7,239 nomenclatures** différentes
- **42 magasins** analysés
- **332,032** quantités totales
- **26,958 déficits** détectés

### Déficits majeurs
- **24,510 cas de surexploitation** (utilisation > stock)
- **2,448 cas de sous-exploitation** (stock > utilisation)
- Déficit total de **198,454 unités**

### Top magasins (par quantité)
1. CNSO : 63,970 unités
2. BST : 29,922 unités
3. TLN : 26,317 unités

## 🧪 Tests

### Tests rapides
```bash
python test_simple.py
```

### Tests unitaires complets
```bash
python tests/test_basic_functionality.py
```

## 📚 Documentation API

### MaterialManager (Classe principale)

```python
class MaterialManager:
    def load_data(file_path: str) -> None
    def calculate_global_statistics() -> InventoryStats
    def analyze_deficits() -> AnalysisResult
    def get_top_magasins(n: int = 10) -> AnalysisResult
    def get_top_nomenclatures(n: int = 10) -> AnalysisResult
    def compare_exploitation_vs_stock() -> AnalysisResult
    def export_data(output_path: str, data_type: str, format: str) -> None
    def generate_visualizations(output_dir: str) -> None
```

### Modèles de données

```python
@dataclass
class InventoryItem:
    nomenclature: str
    magasin: str
    type_donnee: str  # 'U' ou 'C'
    quantite: float

@dataclass
class DeficitItem:
    magasin: str
    nomenclature: str
    quantite_exploitation: float
    quantite_stock: float

    @property
    def deficit(self) -> float  # exploitation - stock
```

## 🔍 Comparaison avec l'ancienne version

| Aspect | Ancienne version | Version refactorisée |
|--------|------------------|---------------------|
| **Architecture** | Monolithique | Modulaire |
| **Duplication** | Code dupliqué | DRY appliqué |
| **Gestion d'erreurs** | Inconsistante | Exceptions spécialisées |
| **Performance** | Recalculs répétés | Cache intelligent |
| **Tests** | Aucun | Suite complète |
| **Extensibilité** | Difficile | Facile |
| **Maintenance** | Complexe | Simple |

## 🚨 Notes importantes

1. **Compatibilité** : Les données doivent avoir des colonnes se terminant par `-U` (exploitation) et `-C` (stock)
2. **Encodage** : Support automatique UTF-8, Latin-1, CP1252
3. **Performance** : Cache activé par défaut, peut être désactivé
4. **Mémoire** : Utilisez `clear_cache()` pour libérer la mémoire

## 🔮 Extensions possibles

- Interface web Streamlit refactorisée
- API REST pour accès distant
- Base de données pour persistance
- Alertes automatiques sur déficits critiques
- Intégration avec systèmes ERP
- Analyses prédictives ML

---

**Cette version refactorisée offre une base solide, maintenable et extensible pour l'analyse des données d'inventaire.**