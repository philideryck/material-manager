def detecter_deficits(df, seuil=0):
    df_deficit = df[df['Stock'] <= seuil]
    return df_deficit
