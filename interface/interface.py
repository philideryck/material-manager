import streamlit as st
import pandas as pd
from modules import importer, classer_magasins, analyse_stock, distribution

def lancer_interface():
    st.title("📦 Application de Gestion de Matériel")

    st.sidebar.header("Chargement des données")
    fichier = st.sidebar.file_uploader("Choisir un fichier (.csv ou .xlsx)", type=["csv", "xlsx"])

    if fichier:
        df = importer.importer_fichier(fichier)
        st.write("Aperçu des données :", df.head())

        # Détection du type de magasin
        df['Type'] = df['Magasin'].apply(classer_magasins.identifier_type_magasin)

        # Sélection du matériel
        materiel_dispo = df['Matériel'].unique().tolist()
        materiel_choisi = st.selectbox("Choisir un matériel à distribuer", materiel_dispo)

        df_filtré = df[df['Matériel'] == materiel_choisi]

        sources = df_filtré[df_filtré['Type'].isin(['disponible', 'central'])]
        cibles = analyse_stock.detecter_deficits(df_filtré[df_filtré['Type'] == 'exploitation'])

        st.subheader("🗂️ Magasins sources (stock positif)")
        st.dataframe(sources)

        st.subheader("📉 Magasins cibles (en déficit)")
        st.dataframe(cibles)

        if not sources.empty and not cibles.empty:
            quantite_max = sources['Stock'].sum()
            quantite = st.slider("Quantité totale à distribuer :", 1, int(quantite_max), 1)

            if st.button("Proposer une distribution"):
                transferts = distribution.proposer_distribution(sources.copy(), cibles.copy(), materiel_choisi, quantite)
                df_transferts = pd.DataFrame(transferts)
                st.success("Distribution générée :")
                st.dataframe(df_transferts)

                st.download_button(
                    "💾 Exporter en CSV",
                    df_transferts.to_csv(index=False).encode('utf-8'),
                    "transferts.csv"
                )
        else:
            st.warning("Aucun magasin source ou cible valide.")
