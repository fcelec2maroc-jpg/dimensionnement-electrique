import streamlit as st
import math
import datetime
import json
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Ingénierie & Chiffrage", layout="wide", initial_sidebar_state="expanded")

# --- DESIGN PROFESSIONNEL (CSS) ---
st.markdown("""
    <style>
    /* Fond général et police */
    .reportview-container { background: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Style des boutons génériques */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: bold; 
        transition: all 0.3s ease;
    }
    
    /* Conteneurs avec effet d'ombre (cartes) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border: 1px solid #e0e0e0 !important;
        background-color: white !important;
        padding: 20px !important;
    }
    
    /* En-têtes */
    h1, h2, h3 { color: #01579b; font-weight: 700; }
    
    /* Alertes (Succès, Info) */
    .stAlert { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
if 'projet' not in st.session_state:
    st.session_state.projet = {
        "info": {"nom": "Chantier Résidentiel"},
        "cables": [],
        "tableaux": {},
        "ks_global": 0.8
    }

# --- FONCTIONS UTILITAIRES ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Chiffrage_FCELEC')
    return output.getvalue()

def sanitize_text(text, max_len=30):
    """Blindage total contre les crashs PDF (Emojis, Arabe, Symboles spéciaux)"""
    if not isinstance(text, str):
        return str(text)
    clean = text.replace("φ", "phi").replace("€", "Euros").replace("é", "e").replace("è", "e").replace("à", "a").replace("É", "E")
    clean = clean.encode('latin-1', 'ignore').decode('latin-1')
    return clean[:max_len] + "..." if len(clean) > max_len else clean

# --- CLASSE PDF PROFESSIONNELLE ---
class FCELEC_Report(FPDF):
    def header(self):
        try: self.image("logoFCELEC.png", 10, 8, 25)
        except: pass
        self.set_font("Helvetica", "B", 14)
        self.cell(30)
        self.cell(130, 8, "DOSSIER TECHNIQUE ELECTRIQUE", border=0, ln=0, align="C")
        self.set_font("Helvetica", "I", 9)
        self.cell(30, 8, f"{datetime.date.today().strftime('%d/%m/%Y')}", border=0, ln=1, align="R")
        self.set_font("Helvetica", "I", 9)
        self.cell(30)
        self.cell(130, 5, "Note de calcul conforme a la norme NF C 15-100", border=0, ln=1, align="C")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.line(10, 282, 200, 282)
        # ⬇️ MODIFICATION DU PIED DE PAGE PDF ICI ⬇️
        self.cell(0, 5, f"FC ELEC - formation et consulting | WhatsApp : +212 6 74 53 42 64 | Page {self.page_no()}", 0, 0, "C")

# --- SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image("logoFCELEC.png", width=250)
            st.markdown("<h3 style='text-align: center;'>🔐 Portail Ingénierie FC ELEC</h3>", unsafe_allow_html=True)
            user = st.text_input("Identifiant")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("Authentification", use_container_width=True):
                if "passwords" in st.secrets and user in st.secrets["passwords"] and pw == st.secrets["passwords"][user]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Accès refusé. Identifiants incorrects.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.markdown("### 💾 GESTION DE PROJET")
    
    st.sidebar.info(f"📁 Projet actif : **{st.session_state.projet['info']['nom']}**")

    projet_json = json.dumps(st.session_state.projet, indent=4)
    st.sidebar.download_button("📥 Sauvegarder Projet (.json)", data=projet_json, file_name=f"{sanitize_text(st.session_state.projet['info']['nom'])}.json", mime="application/json", use_container_width=True)
    
    fichier_charge = st.sidebar.file_uploader("📂 Charger un Projet", type=['json'])
    if fichier_charge is not None:
        try:
            donnees = json.load(fichier_charge)
            if donnees != st.session_state.projet:
                st.session_state.projet = donnees
                st.sidebar.success("✅ Projet chargé avec succès !")
                st.rerun()
        except:
            st.sidebar.error("Fichier invalide.")

    st.sidebar.markdown("---")
    
    # ⬇️ ORDRE DU MENU MODIFIÉ ICI ⬇️
    menu = st.sidebar.radio("Navigation :", [
        "📚 1. Catalogue des Formations",
        "🔌 2. Carnet de Câbles",
        "🏢 3. Bilan de Puissance",
        "💰 4. Nomenclature & Devis",
        "📉 5. Outils (Cos φ & IRVE)"
    ])

    # --- SECTION PUBLICITAIRE FC ELEC (SIDEBAR) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>🎓 FORMATIONS EXPERT</h3>", unsafe_allow_html=True)
    
    st.sidebar.markdown("""
        <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="color: white; font-weight: bold; margin-bottom: 5px; font-size: 1.1em;">🚀 Boostez votre carrière !</p>
            <p style="color: #e1f5fe; font-size: 0.85em; margin: 0;">Devenez un expert recherché avec nos formations certifiantes.</p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none;">
            <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em; transition: 0.3s;">🟢 WHATSAPP</div>
        </a>
        <a href="https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/" target="_blank" style="text-decoration: none;">
            <div style="background-color: #0077B5; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🔵 LINKEDIN</div>
        </a>
        <a href="https://www.facebook.com/profile.php?id=61586577760070" target="_blank" style="text-decoration: none;">
            <div style="background-color: #1877F2; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🔵 FACEBOOK</div>
        </a>
        <a href="https://www.youtube.com/@FCELECACADEMY" target="_blank" style="text-decoration: none;">
            <div style="background-color: #FF0000; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🔴 YOUTUBE</div>
        </a>
    """, unsafe_allow_html=True)

    # =========================================================
    # MODULE 1 : CATALOGUE DES FORMATIONS (EN PREMIER)
    # =========================================================
    if menu == "📚 1. Catalogue des Formations":
        st.markdown("<h1 style='text-align: center; color: #01579b;'>📚 FC ELEC ACADEMY</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2em; color: #555;'>Formations pratiques et certifiantes en Ingénierie Électrique.</p>", unsafe_allow_html=True)
        st.markdown("---")

        if "base_inscriptions" not in st.session_state:
            st.session_state.base_inscriptions = []

        tab_catalogue, tab_inscription = st.tabs(["📖 Catalogue & PDF", "📝 Formulaire de Réservation"])

        with tab_catalogue:
            def charger_pdf(chemin_fichier):
                try:
                    with open(chemin_fichier, "rb") as pdf_file:
                        return pdf_file.read()
                except FileNotFoundError:
                    return b"Fichier non trouve. Veuillez contacter l'administration."

            st.markdown("### 🎯 Nos Domaines d'Expertise")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; text-align: center; height: 220px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">⚡</div>
                    <h4 style="color: #0288d1; margin-top: 0;">Installations CFO (Caneco)</h4>
                    <p style="font-size:0.9em; color: #666;">Conception experte selon les normes NFCs/UTEs via Caneco BT / HT.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN CONCEPTION DES INSTALLATIONS ÉLECTRIQUES CFO CANECO BT-HT.pdf"), file_name="Plan_CFO.pdf", mime="application/pdf", use_container_width=True)
            
            with col2:
                st.markdown("""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; text-align: center; height: 220px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">🏙️</div>
                    <h4 style="color: #0288d1; margin-top: 0;">Réseaux HTA-BT-EP</h4>
                    <p style="font-size:0.9em; color: #666;">Conception de réseaux urbains et lotissements avec AutoCAD & Caneco.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN CONCEPTION DES RÉSEAUX DE DISTRIBUTION HT-BT-EP.pdf"), file_name="Plan_Reseaux.pdf", mime="application/pdf", use_container_width=True)

            with col3:
                st.markdown("""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; text-align: center; height: 220px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">☀️</div>
                    <h4 style="color: #0288d1; margin-top: 0;">Solaire Photovoltaïque</h4>
                    <p style="font-size:0.9em; color: #666;">Dimensionnement et modélisation avancée de centrales sur PV SYST.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES SYSTEMES PHOTOVOLTAÏQUE.pdf"), file_name="Plan_Solaire.pdf", mime="application/pdf", use_container_width=True)

            st.write("")
            col4, col5, col6 = st.columns(3)

            with col4:
                st.markdown("""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; text-align: center; height: 220px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">💡</div>
                    <h4 style="color: #0288d1; margin-top: 0;">Éclairage (DIALux EVO)</h4>
                    <p style="font-size:0.9em; color: #666;">Étude photométrique pointue selon les normes EN 13-201 & 12464-1.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ECLAIRAGE INTERIEUR ET EXTERIEUR 2025.pdf"), file_name="Plan_Eclairage.pdf", mime="application/pdf", use_container_width=True)

            with col5:
                st.markdown("""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; text-align: center; height: 220px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="font-size: 2.5em; margin-bottom: 10px;">📡</div>
                    <h4 style="color: #0288d1; margin-top: 0;">Télécommunications</h4>
                    <p style="font-size:0.9em; color: #666;">Infrastructures génie civil, Fibre Optique et dimensionnement PTT.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES RESEAUX DE TELECOMS.pdf"), file_name="Plan_Telecoms.pdf", mime="application/pdf", use_container_width=True)

        with tab_inscription:
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            with st.container(border=True):
                st.markdown("<h3 style='color: #01579b;'>📝 Demande d'Inscription / Devis</h3>", unsafe_allow_html=True)
                with st.form("formulaire_inscription"):
                    col_f1, col_f2 = st.columns(2)
                    
                    nom_client = col_f1.text_input("👤 Nom et Prénom *")
                    sexe_client = col_f2.selectbox("🚻 Sexe *", ["Sélectionner", "Homme", "Femme"])
                    
                    email_client = col_f1.text_input("📧 Adresse E-mail *", placeholder="exemple@email.com")
                    pays_client = col_f2.text_input("🌍 Pays de résidence *", placeholder="Ex: Maroc, France, Sénégal...")
                    
                    tel_client = st.text_input("📱 Numéro WhatsApp (avec indicatif) *", placeholder="+212 6 XX XX XX XX")
                    
                    st.markdown("#### 🎯 Votre Projet")
                    formation_choisie = st.selectbox("💡 Quelle formation vous intéresse ? *", [
                        "⚡ Conception des Installations Électriques CFO (Caneco BT-HT)",
                        "🏙️ Conception des Réseaux de Distribution HTA-BT-EP",
                        "☀️ Étude et Conception des Systèmes Solaires Photovoltaïques",
                        "💡 Éclairage Intérieur et Extérieur (DIALux EVO)",
                        "📡 Étude et Conception des Réseaux de Télécommunications",
                        "🏢 Formation Sur-Mesure (Entreprise)"
                    ])
                    
                    st.markdown("<small><i>* Champs obligatoires</i></small>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    soumis = st.form_submit_button("🚀 SOUMETTRE MA CANDIDATURE", type="primary", use_container_width=True)
                    
                    if soumis:
                        if not nom_client or not email_client or not tel_client or not pays_client or sexe_client == "Sélectionner":
                            st.error("⚠️ Veuillez remplir tous les champs obligatoires.")
                        else:
                            try:
                                df_existantes = conn.read(worksheet="Inscriptions", ttl=5)
                            except:
                                df_existantes = pd.DataFrame(columns=["Date", "Nom et Prénom", "Sexe", "E-mail", "Pays", "WhatsApp", "Formation Demandée"])

                            nouvelle_inscription = pd.DataFrame([{
                                "Date": datetime.date.today().strftime("%d/%m/%Y"),
                                "Nom et Prénom": nom_client,
                                "Sexe": sexe_client,
                                "E-mail": email_client,
                                "Pays": pays_client,
                                "WhatsApp": tel_client,
                                "Formation Demandée": formation_choisie
                            }])

                            df_mise_a_jour = pd.concat([df_existantes, nouvelle_inscription], ignore_index=True)
                            conn.update(worksheet="Inscriptions", data=df_mise_a_jour)

                            st.success(f"🎉 Parfait {nom_client} ! Votre demande a été enregistrée de manière sécurisée.")
                            
                            texte_wa = (f"Bonjour FC ELEC !%0AJe souhaite confirmer mon inscription.%0A%0A"
                                        f"📋 *Dossier :*%0A- *Nom :* {nom_client}%0A"
                                        f"- *Pays :* {pays_client}%0A- *E-mail :* {email_client}%0A"
                                        f"🎓 *Formation :* {formation_choisie}")
                            
                            lien_wa = f"https://wa.me/212674534264?text={texte_wa}"
                            
                            st.markdown(f"""
                            <div style="background-color: #e8f5e9; padding: 25px; border-radius: 8px; text-align: center; border: 2px solid #4CAF50; margin-top: 15px;">
                                <h3 style="color: #2e7d32; margin-top:0;">Étape Finale Obligatoire ⏳</h3>
                                <p style="font-size: 1.1em; color: #333;">Veuillez valider votre place en nous envoyant un message WhatsApp :</p>
                                <a href="{lien_wa}" target="_blank" style="display: inline-block; background-color: #25D366; color: white; padding: 15px 30px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 1.2em; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: 0.3s;">
                                    💬 CONFIRMER SUR WHATSAPP
                                </a>
                            </div>
                            """, unsafe_allow_html=True)

            # Espace Admin
            st.markdown("---")
            with st.expander("🔐 Accès Direction FC ELEC"):
                if "admin_connecte" not in st.session_state:
                    st.session_state.admin_connecte = False

                if not st.session_state.admin_connecte:
                    st.info("Espace sécurisé réservé à l'administration.")
                    mot_de_passe = st.text_input("Mot de passe administrateur :", type="password")
                    
                    if st.button("Déverrouiller la base"):
                        if mot_de_passe == "FCELEC2026": 
                            st.session_state.admin_connecte = True
                            st.rerun()
                        else:
                            st.error("❌ Accès refusé.")
                
                if st.session_state.admin_connecte:
                    st.success("✅ Session Admin Ouverte.")
                    if st.button("🔒 Verrouiller la session"):
                        st.session_state.admin_connecte = False
                        st.rerun()

                    st.markdown("#### 📊 Base de données des Inscriptions")
                    try:
                        df_inscrits = conn.read(worksheet="Inscriptions", ttl=5)
                        if df_inscrits.empty:
                            st.warning("Aucun prospect enregistré.")
                        else:
                            st.dataframe(df_inscrits, use_container_width=True)
                            
                            output_excel = BytesIO()
                            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                                df_inscrits.to_excel(writer, index=False, sheet_name='Inscriptions')
                            
                            st.download_button(
                                label="📥 EXPORTER BASE CLIENTS (.XLSX)",
                                data=output_excel.getvalue(),
                                file_name=f"Base_Clients_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                    except Exception as e:
                        st.error("Erreur de connexion à Google Sheets.")

    # =========================================================
    # MODULE 2 : CARNET DE CÂBLES
    # =========================================================
    elif menu == "🔌 2. Carnet de Câbles":
        st.title("🔌 Ingénierie des Lignes (NF C 15-100)")
        
        with st.container(border=True):
            st.markdown("#### 📋 1. Identification du Circuit")
            col_p1, col_p2, col_p3 = st.columns(3)
            nom_p = col_p1.text_input("Nom du Projet", st.session_state.projet["info"]["nom"], key="proj_m1")
            st.session_state.projet["info"]["nom"] = nom_p
            nom_tab_cables = col_p2.text_input("Tableau Source", "TGBT")
            ref_c = col_p3.text_input("Désignation", "Départ Sous-sol")

            st.markdown("---")
            with st.form("ajout_cable"):
                st.markdown("#### ⚙️ 2. Paramètres Techniques")
                c1, c2, c3 = st.columns(3)
                tension = c1.selectbox("Tension", ["230V Mono", "400V Tri"])
                p_w = c2.number_input("Puissance (W)", min_value=0.0, value=3500.0)
                longueur = c3.number_input("Longueur (m)", min_value=1.0, value=50.0)
                
                c5, c6, c7 = st.columns(3)
                nature = c5.selectbox("Métal Conducteur", ["Cuivre", "Aluminium"])
                
                type_cable = c6.selectbox("Type d'Isolant", [
                    "U1000 R2V / RO2V (PR)", 
                    "H07VU / H07VR (PVC)", 
                    "H07RN-F (Souple)", 
                    "XAV / AR2V (Armé)", 
                    "CR1-C1 (Incendie)", 
                    "Câble Solaire DC"
                ])

                type_charge = c7.selectbox("Type d'Application", [
                    "Éclairage (Max 3%)", 
                    "Prises de courant (Max 5%)",
                    "Force Motrice / CVC (Max 5%)",
                    "Ligne Principale (Max 2%)"
                ])
                
                c8, c9 = st.columns(2)
                methode_pose = c8.selectbox("Méthode de Pose de Référence", [
                    "Méthode A (Encastré dans paroi isolante)", 
                    "Méthode B (Sous conduit apparent ou encastré)", 
                    "Méthode C (Câble fixé au mur / apparent)",
                    "Méthode D (Enterré dans le sol)",
                    "Méthode E/F (Chemin de câbles / Air libre)"
                ])
                cos_phi = c9.slider("Facteur de puissance (Cos φ)", 0.7, 1.0, 0.85)

                if st.form_submit_button("Calculer et Mémoriser", use_container_width=True):
                    V = 230 if "230V" in tension else 400
                    rho = 0.0225 if "Cuivre" in nature else 0.036
                    b = 2 if "230V" in tension else 1
                    
                    if "3%" in type_charge: du_max = 3.0
                    elif "2%" in type_charge: du_max = 2.0
                    else: du_max = 5.0

                    Ib = p_w / (V * cos_phi) if b == 2 else p_w / (V * math.sqrt(3) * cos_phi)
                    calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630, 800, 1000]
                    In = next((x for x in calibres if x >= Ib), 1000)
                    
                    sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
                    
                    S_calc_du = (b * rho * longueur * Ib) / ((du_max / 100) * V)
                    S_ret_du = next((s for s in sections if s >= S_calc_du), 300)

                    # Base de données complète des Iz
                    dict_iz = {
                        "Méthode A (Encastré dans paroi isolante)": {1.5: 14.5, 2.5: 19.5, 4: 26, 6: 34, 10: 46, 16: 61, 25: 80, 35: 99, 50: 119, 70: 151, 95: 182, 120: 210, 150: 240, 185: 273, 240: 321, 300: 367},
                        "Méthode B (Sous conduit apparent ou encastré)": {1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 151, 70: 192, 95: 232, 120: 269, 150: 309, 185: 353, 240: 415, 300: 477},
                        "Méthode C (Câble fixé au mur / apparent)": {1.5: 19.5, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 112, 35: 138, 50: 168, 70: 213, 95: 258, 120: 299, 150: 344, 185: 392, 240: 461, 300: 530},
                        "Méthode D (Enterré dans le sol)": {1.5: 22, 2.5: 29, 4: 37, 6: 46, 10: 61, 16: 79, 25: 101, 35: 122, 50: 144, 70: 178, 95: 211, 120: 240, 150: 271, 185: 304, 240: 351, 300: 396},
                        "Méthode E/F (Chemin de câbles / Air libre)": {1.5: 23, 2.5: 31, 4: 42, 6: 54, 10: 75, 16: 100, 25: 135, 35: 169, 50: 207, 70: 268, 95: 328, 120: 382, 150: 441, 185: 506, 240: 599, 300: 693}
                    }
                    
                    k_al = 0.78 if "Aluminium" in nature else 1.0
                    k_mono = 1.15 if "230V" in tension else 1.0
                    
                    S_ret_iz = 300
                    for s in sections:
                        Iz_calc = dict_iz[methode_pose][s] * k_al * k_mono
                        if Iz_calc >= In:
                            S_ret_iz = s
                            break

                    S_ret = max(S_ret_du, S_ret_iz)
                    
                    Iz_reel = dict_iz[methode_pose][S_ret] * k_al * k_mono
                    du_reel_pct = (((b * rho * longueur * Ib) / S_ret) / V) * 100
                    
                    lettre_pose = methode_pose.split(" ")[1]

                    st.session_state.projet["cables"].append({
                        "Tableau": nom_tab_cables, "Repère": ref_c, "Type Câble": type_cable, "Métal": nature, 
                        "Pose": lettre_pose, "Tension": tension, "P(W)": p_w, "Long.(m)": longueur,
                        "Ib(A)": round(Ib, 1), "Calibre(A)": In, "Iz(A)": round(Iz_reel, 1), "Section(mm2)": S_ret, "dU(%)": round(du_reel_pct, 2)
                    })
                    st.success(f"✅ Section retenue : **{S_ret} mm²** (Iz={round(Iz_reel,1)}A, Pose {lettre_pose}) | Disjoncteur: **{In}A**")

        if st.session_state.projet["cables"]:
            st.markdown("### 📑 Carnet de Câbles Généré")
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)
            
            def generate_pdf_cables():
                pdf = FCELEC_Report()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_fill_color(2, 136, 209) # Bleu moderne
                pdf.set_text_color(255, 255, 255)
                titre = sanitize_text(st.session_state.projet['info']['nom']).upper()
                pdf.cell(190, 10, f" CARNET DE CABLES - {titre}", border=0, ln=True, align="C", fill=True)
                pdf.ln(5)
                
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_fill_color(230, 230, 230)
                pdf.set_text_color(0, 0, 0)
                
                headers = ["Tab.", "Repere", "Type Cable", "L(m)", "Ib(A)", "In(A)", "Iz(A)", "Section + Pose", "dU(%)"]
                widths = [15, 25, 25, 12, 15, 15, 15, 50, 18]
                
                for i in range(len(headers)): 
                    pdf.cell(widths[i], 8, headers[i], 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_font("Helvetica", "", 8)
                for row in st.session_state.projet["cables"]:
                    pdf.cell(widths[0], 8, sanitize_text(row.get("Tableau", "TGBT"), 12), 1)
                    pdf.cell(widths[1], 8, sanitize_text(row["Repère"], 18), 1)
                    
                    clean_type = sanitize_text(row.get("Type Câble", "U1000 R2V").split(" (")[0], 25) 
                    pdf.cell(widths[2], 8, clean_type, 1, 0, 'C')
                    
                    pdf.cell(widths[3], 8, str(row["Long.(m)"]), 1, 0, 'C')
                    pdf.cell(widths[4], 8, str(row["Ib(A)"]), 1, 0, 'C')
                    
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(widths[5], 8, f"{row['Calibre(A)']}A", 1, 0, 'C')
                    pdf.set_text_color(0, 128, 0)
                    pdf.cell(widths[6], 8, f"{row.get('Iz(A)', '-')}A", 1, 0, 'C')
                    
                    pdf.set_text_color(255, 100, 0)
                    pdf.cell(widths[7], 8, f"{row['Section(mm2)']} mm2 ({row.get('Pose', 'B')})", 1, 0, 'C')
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(widths[8], 8, str(row["dU(%)"]), 1, 1, 'C')
                return pdf.output()

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("📄 EXPORTER NOTE DE CALCUL (PDF)", type="primary", use_container_width=True):
                st.download_button("📥 Confirmer Téléchargement PDF", bytes(generate_pdf_cables()), f"Note_Calcul_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")
            if col_btn2.button("🗑️ Vider le Carnet", use_container_width=True):
                st.session_state.projet["cables"] = []; st.rerun()

    # =========================================================
    # MODULE 3 : ARCHITECTURE MULTI-TABLEAUX
    # =========================================================
    elif menu == "🏢 3. Bilan de Puissance":
        st.title("🏢 Architecture et Bilan de Puissance")
        
        with st.container(border=True):
            st.markdown("#### 📋 1. Structure du Projet")
            nom_p_m2 = st.text_input("Nom du Projet", st.session_state.projet["info"]["nom"], key="proj_m2")
            st.session_state.projet["info"]["nom"] = nom_p_m2
            
            st.markdown("---")
            col_t1, col_t2 = st.columns([3, 1])
            nouveau_tab = col_t1.text_input("Nom du nouveau Tableau (ex: TD RDC, TGBT)")
            if col_t2.button("➕ Créer Tableau", use_container_width=True) and nouveau_tab:
                if nouveau_tab not in st.session_state.projet["tableaux"]:
                    st.session_state.projet["tableaux"][nouveau_tab] = []
                    st.rerun()

        if st.session_state.projet["tableaux"]:
            onglets = st.tabs(list(st.session_state.projet["tableaux"].keys()) + ["🌍 SYNTHÈSE GLOBALE"])
            
            for i, nom_tab in enumerate(list(st.session_state.projet["tableaux"].keys())):
                with onglets[i]:
                    st.markdown(f"### Gestion du tableau : {nom_tab}")
                    if st.button(f"❌ Supprimer '{nom_tab}'", key=f"del_{nom_tab}"):
                        del st.session_state.projet["tableaux"][nom_tab]
                        st.rerun()

                    with st.container(border=True):
                        with st.form(f"form_{i}"):
                            c1, c2, c3, c4 = st.columns([2,1,1,1])
                            c_nom = c1.text_input("Circuit (ex: Prises Bureau)")
                            c_p = c2.number_input("Puissance (W)", min_value=0.0, value=1000.0)
                            
                            c_type = c3.selectbox("Type", [
                                "Éclairage", "Prises de courant", "Chauffage électrique", 
                                "Climatisation / PAC", "Force Motrice", "Cuisson", 
                                "IRVE (Recharge VE)", "Divers"
                            ])

                            if c_type in ["Éclairage", "Chauffage", "IRVE"]: ku_def = 1.0
                            elif c_type == "Prises de courant": ku_def = 0.5
                            elif c_type == "Cuisson": ku_def = 0.7
                            elif c_type in ["Climatisation / PAC", "Force Motrice"]: ku_def = 0.75
                            else: ku_def = 0.8
                                
                            c_ku = c4.number_input("Facteur Ku", min_value=0.1, max_value=1.0, value=float(ku_def), step=0.05)
                            
                            if st.form_submit_button("➕ Ajouter au tableau"):
                                st.session_state.projet["tableaux"][nom_tab].append({
                                    "Circuit": c_nom, "Type": c_type, "P(W)": c_p, "Ku": c_ku, "P.Abs(W)": int(c_p * c_ku)
                                })
                                st.rerun()
                    
                    circuits = st.session_state.projet["tableaux"].get(nom_tab, [])
                    if circuits:
                        df_tab = pd.DataFrame(circuits)
                        st.dataframe(df_tab, use_container_width=True)
                        st.metric(f"Total Absorbé (Tableau {nom_tab})", f"{df_tab['P.Abs(W)'].sum()} W")

            with onglets[-1]:
                st.markdown("### 🌍 Bilan Bâtiment (TGBT)")
                bilan_global = [{"Tableau": t, "Puissance Absorbée (W)": sum(c["P.Abs(W)"] for c in circs)} for t, circs in st.session_state.projet["tableaux"].items()]
                
                if bilan_global:
                    df_g = pd.DataFrame(bilan_global)
                    st.dataframe(df_g, use_container_width=True)
                    p_totale = df_g["Puissance Absorbée (W)"].sum()
                    
                    ks_global = st.slider("Coefficient de Foisonnement Global (Ks)", 0.4, 1.0, st.session_state.projet.get("ks_global", 0.8))
                    st.session_state.projet["ks_global"] = ks_global
                    
                    p_appel = int(p_totale * ks_global)
                    kva_estime = round(p_appel / 0.8 / 1000, 1)
                    
                    col_res1, col_res2 = st.columns(2)
                    col_res1.success(f"**⚡ PUISSANCE ACTIVE (kW) : {p_appel/1000:.1f} kW**")
                    col_res2.info(f"**🏢 PUISSANCE APPARENTE (kVA) : {kva_estime} kVA**")

                    def generate_pdf_bilan():
                        pdf = FCELEC_Report()
                        pdf.set_auto_page_break(auto=True, margin=15)
                        pdf.add_page()
                        
                        pdf.set_font("Helvetica", "B", 14)
                        titre = sanitize_text(st.session_state.projet['info']['nom']).upper()
                        pdf.set_text_color(2, 136, 209)
                        pdf.cell(190, 10, f"BILAN DE PUISSANCE - {titre}", ln=True, align="C")
                        pdf.set_text_color(0, 0, 0)
                        pdf.ln(5)

                        for tab_name, circs in st.session_state.projet["tableaux"].items():
                            if not circs: continue
                            pdf.set_font("Helvetica", "B", 11)
                            pdf.set_fill_color(220, 220, 220)
                            pdf.cell(190, 8, f" TABLEAU : {sanitize_text(tab_name)}", border=1, ln=True, fill=True)
                            
                            pdf.set_font("Helvetica", "B", 9)
                            pdf.cell(60, 6, "Circuit", 1)
                            pdf.cell(50, 6, "Type", 1, 0, 'C')
                            pdf.cell(30, 6, "P.Inst (W)", 1, 0, 'C')
                            pdf.cell(20, 6, "Ku", 1, 0, 'C')
                            pdf.cell(30, 6, "P.Abs (W)", 1, 1, 'C')
                            
                            pdf.set_font("Helvetica", "", 9)
                            sous_total = 0
                            for c in circs:
                                pdf.cell(60, 6, sanitize_text(c['Circuit'], 30), 1)
                                pdf.cell(50, 6, sanitize_text(c['Type'], 25), 1, 0, 'C')
                                pdf.cell(30, 6, str(c['P(W)']), 1, 0, 'C')
                                pdf.cell(20, 6, str(c['Ku']), 1, 0, 'C')
                                pdf.cell(30, 6, str(c['P.Abs(W)']), 1, 1, 'C')
                                sous_total += c['P.Abs(W)']
                            
                            pdf.set_font("Helvetica", "I", 9)
                            pdf.cell(190, 6, f"Sous-total absorbé ({sanitize_text(tab_name)}) : {sous_total} W", border='B', ln=True, align="R")
                            pdf.ln(4)

                        pdf.ln(5)
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.set_fill_color(2, 136, 209)
                        pdf.set_text_color(255, 255, 255)
                        pdf.cell(190, 10, f"PUISSANCE ACTIVE MAXIMALE (Ks={ks_global}) : {p_appel} W", border=0, ln=True, align="C", fill=True)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(190, 10, f"PUISSANCE SOUSCRITE ESTIMEE (Cos phi 0.8) : {kva_estime} kVA", border=1, ln=True, align="C", fill=True)
                        return pdf.output()

                    if st.button("📄 EXPORTER BILAN (PDF)", type="primary", use_container_width=True):
                        st.download_button("📥 Confirmer Téléchargement", bytes(generate_pdf_bilan()), f"Bilan_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")

    # =========================================================
    # MODULE 4 : NOMENCLATURE & DEVIS
    # =========================================================
    elif menu == "💰 4. Nomenclature & Devis":
        st.title("💰 Chiffrage et Quantitatifs")
        nomenclatures = []
        
        for cab in st.session_state.projet["cables"]:
            nature = cab.get("Métal", "Cuivre")
            type_c = cab.get("Type Câble", "U1000 R2V").split(" (")[0]
            nomenclatures.append({"Catégorie": "Câble", "Désignation": f"Câble {nature} {type_c} - {cab['Section(mm2)']} mm2", "Quantité": cab["Long.(m)"], "Unité": "m", "Prix Unitaire HT": 15.0})
            nomenclatures.append({"Catégorie": "Protection", "Désignation": f"Disjoncteur TGBT {cab['Calibre(A)']}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 80.0})

        for tab, circs in st.session_state.projet["tableaux"].items():
            for c in circs:
                cal_estime = 16 if c["P(W)"] <= 3500 else 20 if c["P(W)"] <= 4500 else 32
                nomenclatures.append({"Catégorie": "Protection", "Désignation": f"Disjoncteur Modulaire {cal_estime}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 65.0})

        if not nomenclatures:
            st.info("Veuillez générer des lignes ou des bilans dans les modules précédents.")
        else:
            with st.container(border=True):
                st.markdown("### 🛒 Édition des prix")
                df_nom = pd.DataFrame(nomenclatures)
                df_nom["Prix Unitaire HT"] = pd.to_numeric(df_nom["Prix Unitaire HT"], errors='coerce').fillna(0)
                df_nom["Quantité"] = pd.to_numeric(df_nom["Quantité"], errors='coerce').fillna(0)
                
                df_grouped = df_nom.groupby(["Catégorie", "Désignation", "Unité"], as_index=False).agg({"Quantité": "sum", "Prix Unitaire HT": "mean"})
                
                df_edited = st.data_editor(
                    df_grouped,
                    key="editeur_devis",
                    column_config={"Prix Unitaire HT": st.column_config.NumberColumn("Prix U. HT (MAD)", format="%.2f")},
                    hide_index=True, use_container_width=True
                )
                
                df_edited["Total HT"] = df_edited["Quantité"] * df_edited["Prix Unitaire HT"]
                total_ht = df_edited["Total HT"].sum()
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                c1.metric("💰 Total Matériel (HT)", f"{total_ht:,.2f} MAD")
                c2.metric("💳 Total Matériel (TTC 20%)", f"{total_ht * 1.20:,.2f} MAD")

                st.download_button("📊 EXPORTER LE DEVIS VERS EXCEL (.XLSX)", data=to_excel(df_edited), file_name=f"Devis_{sanitize_text(st.session_state.projet['info']['nom'])}.xlsx", type="primary", use_container_width=True)

    # =========================================================
    # MODULE 5 : OUTILS
    # =========================================================
    elif menu == "📉 5. Outils (Cos φ & IRVE)":
        st.title("🛠️ Outils Pratiques")
        onglets = st.tabs(["📉 Batterie Condensateurs", "🚘 Bornes IRVE"])
        with onglets[0]:
            with st.container(border=True):
                st.markdown("### Compensation d'Energie Réactive")
                p_kw = st.number_input("Puissance de l'installation (kW)", value=100.0)
                c1, c2 = st.columns(2)
                cos_i = c1.slider("Cos φ Initial (actuel)", 0.5, 0.95, 0.75)
                cos_v = c2.slider("Cos φ Visé (cible)", 0.9, 1.0, 0.95)
                qc = p_kw * (math.tan(math.acos(cos_i)) - math.tan(math.acos(cos_v)))
                st.info(f"Puissance réactive à installer : **{math.ceil(qc)} kVAR**")
            
        with onglets[1]:
            with st.container(border=True):
                st.markdown("### Infrastructures de Recharge (IRVE)")
                p_b = st.selectbox("Puissance de la borne", ["7.4 kW (32A Monophasé)", "22 kW (32A Triphasé)"])
                st.warning("Rappel Norme : Protection Différentielle 30mA Type B ou Type A-EV exigée. Câblage 10 mm² minimum recommandé.")

    # ---------------------------------------------------------
    # PIED DE PAGE GLOBAL
    # ---------------------------------------------------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 25px; border-radius: 12px; text-align: center; border-left: 6px solid #0288d1; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="color: #01579b; margin-top: 0; font-size: 1.4em;">🎓 L'ingénierie vous passionne ?</h3>
        <p style="color: #0277bd; font-size: 1.1em; margin-bottom: 20px;">Devenez un expert technique avec <b>FC ELEC ACADEMY</b>. Formations pratiques, certifiantes et sur logiciels pro.</p>
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none; background-color: #FF4B4B; color: white; padding: 12px 25px; border-radius: 8px; font-weight: bold; transition: 0.3s; display: inline-block;">
            👉 Discuter de mon projet de formation
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    foot1, foot2, foot3, foot4 = st.columns(4)
    
    with foot1:
        st.markdown("<h4 style='color:#01579b;'>🎓 FC ELEC</h4>", unsafe_allow_html=True)
        st.write("Ingénierie, Formation & Consulting")
        st.write("📍 Rabat, Maroc")
        
    with foot2:
        st.markdown("<h4 style='color:#01579b;'>📱 Contact</h4>", unsafe_allow_html=True)
        st.write("WhatsApp: [+212 674-534264](https://wa.me/212674534264)")
        st.write("Email: [fcelec2.maroc@gmail.com](mailto:fcelec2.maroc@gmail.com)")
        
    with foot3:
        st.markdown("<h4 style='color:#01579b;'>🌐 Réseaux</h4>", unsafe_allow_html=True)
        st.markdown("[LinkedIn](https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/) | [YouTube](https://www.youtube.com/@FCELECACADEMY)")
        st.markdown("[Facebook](https://www.facebook.com/profile.php?id=61586577760070)")

    with foot4:
        st.markdown("<h4 style='color:#01579b;'>🚀 Nos Services</h4>", unsafe_allow_html=True)
        st.write("Études de conception")
        st.write("Formations certifiantes")

    st.markdown(
        """
        <div style="background-color: #0e1117; padding: 15px; border-radius: 8px; text-align: center; border-top: 3px solid #0288d1; margin-top: 20px;">
            <p style="color: white; font-size: 0.85em; margin: 0; font-weight: 500;">
                © 2026 <b>FC ELEC EXPERT</b> | Plateforme d'Ingénierie Électrique.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    if st.sidebar.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()
