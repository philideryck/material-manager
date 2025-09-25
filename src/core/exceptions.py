"""
Exceptions personnalisées pour le gestionnaire de matériel.
"""


class MaterialManagerError(Exception):
    """Exception de base pour le gestionnaire de matériel."""
    pass


class DataImportError(MaterialManagerError):
    """Erreur lors de l'importation des données."""
    pass


class DataValidationError(MaterialManagerError):
    """Erreur de validation des données."""
    pass


class DataTransformationError(MaterialManagerError):
    """Erreur lors de la transformation des données."""
    pass


class AnalysisError(MaterialManagerError):
    """Erreur lors de l'analyse des données."""
    pass


class VisualizationError(MaterialManagerError):
    """Erreur lors de la création de visualisations."""
    pass


class ConfigurationError(MaterialManagerError):
    """Erreur de configuration."""
    pass