def proposer_distribution(df_sources, df_cibles, materiel, quantite):
    distributions = []
    for idx, cible in df_cibles.iterrows():
        besoin = abs(cible['Stock'])
        if quantite <= 0:
            break
        for i, source in df_sources.iterrows():
            dispo = source['Stock']
            if dispo > 0:
                transfert = min(dispo, besoin, quantite)
                if transfert > 0:
                    distributions.append({
                        'source': source['Magasin'],
                        'destination': cible['Magasin'],
                        'materiel': materiel,
                        'quantite': transfert
                    })
                    df_sources.at[i, 'Stock'] -= transfert
                    quantite -= transfert
                    besoin -= transfert
    return distributions
