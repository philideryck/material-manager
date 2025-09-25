def proposer_distribution(df_sources, df_cibles, materiel, quantite):
    """
    Propose une distribution optimale du matériel entre les magasins sources et cibles.

    Args:
        df_sources: DataFrame des magasins avec du stock disponible
        df_cibles: DataFrame des magasins en déficit
        materiel: Type de matériel à distribuer
        quantite: Quantité totale à distribuer

    Returns:
        list: Liste des transferts proposés
    """
    distributions = []
    quantite_restante = quantite

    for idx, cible in df_cibles.iterrows():
        if quantite_restante <= 0:
            break

        besoin = abs(cible['Stock'])
        besoin_restant = besoin

        for i, source in df_sources.iterrows():
            if quantite_restante <= 0 or besoin_restant <= 0:
                break

            dispo = source['Stock']
            if dispo > 0:
                transfert = min(dispo, besoin_restant, quantite_restante)
                if transfert > 0:
                    distributions.append({
                        'Source': source['Magasin'],
                        'Destination': cible['Magasin'],
                        'Matériel': materiel,
                        'Quantité': transfert,
                        'Stock source avant': dispo,
                        'Stock source après': dispo - transfert,
                        'Déficit cible avant': cible['Stock'],
                        'Déficit cible après': cible['Stock'] + transfert
                    })
                    df_sources.at[i, 'Stock'] -= transfert
                    quantite_restante -= transfert
                    besoin_restant -= transfert

    return distributions

def calculer_statistiques_distribution(distributions):
    """
    Calcule les statistiques d'une distribution.

    Args:
        distributions: Liste des transferts

    Returns:
        dict: Statistiques de la distribution
    """
    if not distributions:
        return {
            'total_transfere': 0,
            'nombre_transferts': 0,
            'magasins_sources_utilises': 0,
            'magasins_cibles_servis': 0
        }

    total_transfere = sum(t['Quantité'] for t in distributions)
    nombre_transferts = len(distributions)
    sources_uniques = len(set(t['Source'] for t in distributions))
    cibles_uniques = len(set(t['Destination'] for t in distributions))

    return {
        'total_transfere': total_transfere,
        'nombre_transferts': nombre_transferts,
        'magasins_sources_utilises': sources_uniques,
        'magasins_cibles_servis': cibles_uniques
    }
