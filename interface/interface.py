import streamlit as st
import pandas as pd
from modules import importer, classer_magasins, analyse_stock, distribution

def lancer_interface():
    st.set_page_config(
        page_title="Gestionnaire de Matériel",
        page_icon="📦",
        layout="wide"
    )

    st.title("📦 Application de Gestion de Matériel")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("📂 Chargement des données")
        fichier = st.file_uploader(
            "Choisir un fichier (.csv ou .xlsx)",
            type=["csv", "xlsx"],
            help="Le fichier doit contenir les colonnes: Magasin, Matériel, Stock"
        )

        if fichier:
            try:
                with st.spinner("Chargement du fichier en cours..."):
                    df = importer.importer_fichier(fichier)

                importer.valider_colonnes(df)

                st.success(f"✅ Fichier chargé avec succès!")
                st.info(f"📊 {len(df)} lignes chargées")

                df['Type'] = df['Magasin'].apply(classer_magasins.identifier_type_magasin)

                stats_globales = analyse_stock.analyser_stock_global(df)

                st.markdown("### 📈 Statistiques globales")
                col_stat1, col_stat2, col_stat3 = st.columns(3)

                with col_stat1:
                    st.metric("Matériels", stats_globales['total_materiel'])
                    st.metric("Magasins", stats_globales['total_magasins'])

                with col_stat2:
                    st.metric("Stock positif", stats_globales['stock_total_positif'])
                    st.metric("Déficit total", stats_globales['deficit_total'])

                with col_stat3:
                    st.metric("Magasins en déficit", stats_globales['magasins_en_deficit'])
                    st.metric("Magasins avec stock", stats_globales['magasins_avec_stock'])

            except Exception as e:
                st.error(f"❌ Erreur lors du chargement: {str(e)}")
                return

    with col2:
        if 'df' in locals() and not df.empty:
            st.header("🎯 Distribution de Matériel")

            materiel_dispo = sorted(df['Matériel'].unique().tolist())
            materiel_choisi = st.selectbox(
                "Choisir un matériel à distribuer",
                materiel_dispo,
                help="Sélectionnez le type de matériel à redistribuer"
            )

            if materiel_choisi:
                df_filtré = df[df['Matériel'] == materiel_choisi].copy()

                sources = df_filtré[df_filtré['Type'].isin(['disponible', 'central']) & (df_filtré['Stock'] > 0)]
                cibles = analyse_stock.detecter_deficits(df_filtré[df_filtré['Type'] == 'exploitation'])

                tab1, tab2, tab3 = st.tabs(["🗂️ Sources", "📉 Déficits", "🚚 Distribution"])

                with tab1:
                    if not sources.empty:
                        st.success(f"✅ {len(sources)} magasin(s) source(s) disponible(s)")
                        sources_display = sources[['Magasin', 'Stock', 'Type']].sort_values('Stock', ascending=False)
                        st.dataframe(sources_display, use_container_width=True)
                        st.info(f"📦 Stock total disponible: {sources['Stock'].sum()}")
                    else:
                        st.warning("⚠️ Aucun magasin source avec stock positif")

                with tab2:
                    if not cibles.empty:
                        st.error(f"❗ {len(cibles)} magasin(s) en déficit")
                        cibles_display = cibles[['Magasin', 'Stock', 'Déficit']].sort_values('Déficit', ascending=False)
                        st.dataframe(cibles_display, use_container_width=True)
                        st.info(f"📉 Déficit total: {cibles['Déficit'].sum()}")
                    else:
                        st.success("✅ Aucun magasin en déficit")

                with tab3:
                    if not sources.empty and not cibles.empty:
                        quantite_max = min(sources['Stock'].sum(), cibles['Déficit'].sum())

                        st.markdown("### ⚙️ Configuration de la distribution")

                        col_qty1, col_qty2 = st.columns(2)
                        with col_qty1:
                            quantite = st.slider(
                                "Quantité totale à distribuer:",
                                min_value=1,
                                max_value=int(quantite_max),
                                value=min(10, int(quantite_max)),
                                help=f"Maximum disponible: {quantite_max}"
                            )

                        with col_qty2:
                            st.metric("Stock disponible", sources['Stock'].sum())
                            st.metric("Besoin total", cibles['Déficit'].sum())

                        if st.button("🚚 Proposer une distribution", type="primary", use_container_width=True):
                            with st.spinner("Calcul de la distribution en cours..."):
                                try:
                                    transferts = distribution.proposer_distribution(
                                        sources.copy(), cibles.copy(), materiel_choisi, quantite
                                    )

                                    if transferts:
                                        df_transferts = pd.DataFrame(transferts)
                                        stats = distribution.calculer_statistiques_distribution(transferts)

                                        st.success("✅ Distribution générée avec succès!")

                                        col_res1, col_res2 = st.columns(2)
                                        with col_res1:
                                            st.metric("Total transféré", stats['total_transfere'])
                                            st.metric("Nombre de transferts", stats['nombre_transferts'])

                                        with col_res2:
                                            st.metric("Sources utilisées", stats['magasins_sources_utilises'])
                                            st.metric("Cibles servies", stats['magasins_cibles_servis'])

                                        st.dataframe(df_transferts, use_container_width=True)

                                        csv_data = df_transferts.to_csv(index=False).encode('utf-8')
                                        st.download_button(
                                            label="💾 Exporter les transferts en CSV",
                                            data=csv_data,
                                            file_name=f"transferts_{materiel_choisi.replace(' ', '_').lower()}.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                                    else:
                                        st.warning("⚠️ Aucun transfert possible avec les paramètres actuels")

                                except Exception as e:
                                    st.error(f"❌ Erreur lors de la génération: {str(e)}")
                    else:
                        if sources.empty:
                            st.warning("⚠️ Aucun magasin source disponible")
                        if cibles.empty:
                            st.info("ℹ️ Aucun magasin en déficit")

    st.markdown("---")
    with st.expander("ℹ️ Guide d'utilisation"):
        st.markdown("""
        **Types de magasins:**
        - 🏪 **Exploitation** (`-U`): Magasins en exploitation, souvent en déficit
        - 📦 **Disponible** (`-C`): Magasins avec du stock mobilisable
        - 🏢 **Central** (sans suffixe): Stock principal

        **Comment utiliser:**
        1. Chargez un fichier CSV/Excel avec les colonnes: Magasin, Matériel, Stock
        2. Consultez les statistiques globales
        3. Sélectionnez un matériel à distribuer
        4. Vérifiez les sources et déficits
        5. Configurez et lancez la distribution
        6. Exportez les résultats
        """)

    st.markdown("---")
    st.caption("Application développée pour optimiser la gestion des stocks et transferts de matériel")
