def detecter_deficits(df, seuil=0):
    """
    Détecte les magasins en déficit selon un seuil donné.

    Args:
        df: DataFrame contenant les données de stock
        seuil: Seuil en dessous duquel un stock est considéré en déficit (défaut: 0)

    Returns:
        DataFrame: Magasins en déficit triés par déficit décroissant
    """
    df_deficit = df[df['Stock'] <= seuil].copy()

    df_deficit = df_deficit.sort_values('Stock', ascending=True)

    df_deficit['Déficit'] = df_deficit['Stock'].abs()

    return df_deficit

def analyser_stock_global(df):
    """
    Analyse globale du stock par type de magasin et matériel.

    Args:
        df: DataFrame contenant les données de stock

    Returns:
        dict: Statistiques globales du stock
    """
    stats = {
        'total_materiel': df['Matériel'].nunique(),
        'total_magasins': df['Magasin'].nunique(),
        'stock_total_positif': df[df['Stock'] > 0]['Stock'].sum(),
        'deficit_total': abs(df[df['Stock'] < 0]['Stock'].sum()),
        'magasins_en_deficit': len(df[df['Stock'] < 0]),
        'magasins_avec_stock': len(df[df['Stock'] > 0])
    }

    return stats

def detecter_surplus(df, seuil_surplus=10):
    """
    Détecte les magasins avec un surplus important.

    Args:
        df: DataFrame contenant les données de stock
        seuil_surplus: Seuil au-dessus duquel un stock est considéré en surplus

    Returns:
        DataFrame: Magasins avec surplus
    """
    df_surplus = df[df['Stock'] >= seuil_surplus].copy()
    df_surplus = df_surplus.sort_values('Stock', ascending=False)
    return df_surplus
