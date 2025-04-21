def identifier_type_magasin(nom_magasin: str) -> str:
    if nom_magasin.endswith('-U'):
        return 'exploitation'
    elif nom_magasin.endswith('-C'):
        return 'disponible'
    else:
        return 'central'
