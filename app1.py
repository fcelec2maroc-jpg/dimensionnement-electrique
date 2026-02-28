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

# --- DESIGN PROFESSIONNEL (CSS) PREMIUM ---
st.markdown("""
    <style>
    /* Fond général et police */
    .reportview-container { background: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Style des boutons génériques */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: bold; 
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    
    /* Conteneurs avec effet d'ombre (cartes) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border: 1px solid #e0e0e0 !important;
        background-color: white !important;
        padding: 25px !important;
    }
    
    /* En-têtes */
    h1 { color: #01579b; font-weight: 800; letter-spacing: -0.5px; }
    h2, h3, h4 { color: #0277bd; font-weight: 700; }
    
    /* Cartes animées pour le catalogue */
    .course-card {
        background: white; 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 20px; 
        text-align: center; 
        height: 230px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .course-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 20px rgba(1, 87, 155, 0.15);
        border-color: #0288d1;
    }
    
    /* Cartes de métriques (Dashboards) */
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f0f8ff);
        border-left: 5px solid #0288d1;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-title { font-size: 1.1em; color: #546e7a; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .metric-value { font-size: 2em; color: #01579b; font-weight: 800; margin: 0; }
    
    /* Alertes (Succès, Info) */
    .stAlert { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
if 'projet' not in st.session_state:
    st.session_state.projet = {
        "info": {"nom": "Nouveau Projet FC ELEC"},
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
        
        # Ligne verticale bleue
        self.set_draw_color(2, 136, 209)
        self.set_line_width(0.6)
        self.line(38, 8, 38, 23)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        
        self.set_font("Helvetica", "B", 14)
        self.cell(30)
        self.cell(130, 8, "DOSSIER TECHNIQUE ELECTRIQUE", border=0, ln=0, align="C")
        self.set_font("Helvetica", "I", 9)
        self.cell(30, 8, f"{datetime.date.today().strftime('%d/%m/%Y')}", border=0, ln=1, align="R")
        self.set_font("Helvetica", "I", 9)
        self.cell(30)
        self.cell(130, 5, "Note de calcul conforme a la norme NF C 15-100", border=0, ln=1, align="C")
        
        # Ligne horizontale bleue
        self.set_draw_color(2, 136, 209)
        self.line(10, 26, 200, 26)
        self.set_draw_color(0, 0, 0)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.line(10, 282, 200, 282)
        self.cell(0, 5, f"FC ELEC - formation et consulting | WhatsApp : +212 6 74 53 42 64 | Page {self.page_no()}", 0, 0, "C")

# --- SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.image("logoFCELEC.png", width=200)
                st.markdown("<h3 style='text-align: center; color:#01579b;'>🔐 Accès Logiciel</h3>", unsafe_allow_html=True)
                user = st.text_input("Identifiant", placeholder="Entrez votre identifiant")
                pw = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Connexion Sécurisée", use_container_width=True, type="primary"):
                    if "passwords" in st.secrets and user in st.secrets["passwords"] and pw == st.secrets["passwords"][user]:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects. Veuillez réessayer.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.image("logoFCELEC.png", use_container_width=True)
        st.markdown("---")
        st.markdown("### 💾 ESPACE PROJET")
        
        st.info(f"📁 **Projet en cours :**\n\n{st.session_state.projet['info']['nom']}")

        projet_json = json.dumps(st.session_state.projet, indent=4)
        st.download_button("📥 Sauvegarder (.json)", data=projet_json, file_name=f"Projet_{sanitize_text(st.session_state.projet['info']['nom'])}.json", mime="application/json", use_container_width=True)
        
        fichier_charge = st.file_uploader("📂 Charger un Projet", type=['json'], label_visibility="collapsed")
        if fichier_charge is not None:
            try:
                donnees = json.load(fichier_charge)
                if donnees != st.session_state.projet:
                    st.session_state.projet = donnees
                    st.success("✅ Projet chargé !")
                    st.rerun()
            except:
                st.error("Fichier corrompu.")

        st.markdown("---")
        st.markdown("### 🧭 NAVIGATION")
        menu = st.radio("Menu principal :", [
            "📚 1. Catalogue des Formations",
            "🔌 2. Carnet de Câbles",
            "🏢 3. Bilan de Puissance",
            "💰 4. Nomenclature & Devis",
            "📉 5. Outils (Cos φ & IRVE)"
        ], label_visibility="collapsed")

        st.markdown("---")
        st.markdown("""
            <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="color: white; font-weight: bold; margin-bottom: 5px; font-size: 1.1em;">🚀 Boostez votre carrière !</p>
                <p style="color: #e1f5fe; font-size: 0.85em; margin: 0;">Devenez expert avec nos formations.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none;">
                <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🟢 WHATSAPP</div>
            </a>
            <a href="https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/" target="_blank" style="text-decoration: none;">
                <div style="background-color: #0077B5; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🔵 LINKEDIN</div>
            </a>
            <a href="https://www.youtube.com/@FCELECACADEMY" target="_blank" style="text-decoration: none;">
                <div style="background-color: #FF0000; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold; font-size: 0.9em;">🔴 YOUTUBE</div>
            </a>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔴 DÉCONNEXION", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # =========================================================
    # MODULE 1 : CATALOGUE DES FORMATIONS
    # =========================================================
    if menu == "📚 1. Catalogue des Formations":
        st.markdown("<h1 style='text-align: center;'>📚 FC ELEC ACADEMY</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2em; color: #555;'>L'excellence de la formation continue en Ingénierie Électrique.</p>", unsafe_allow_html=True)
        st.divider()

        if "base_inscriptions" not in st.session_state:
            st.session_state.base_inscriptions = []

        tab_catalogue, tab_inscription = st.tabs(["📖 Catalogue & Programmes", "📝 Inscription & Devis"])

        with tab_catalogue:
            def charger_pdf(chemin_fichier):
                try:
                    with open(chemin_fichier, "rb") as pdf_file:
                        return pdf_file.read()
                except FileNotFoundError:
                    return b"Fichier indisponible."

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div class="course-card">
                    <div style="font-size: 3em; margin-bottom: 10px;">⚡</div>
                    <h4 style="margin-top: 0;">Installations CFO (Caneco)</h4>
                    <p style="font-size:0.9em; color: #666;">Conception experte (NFCs/UTEs) via Caneco BT / HT.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN CONCEPTION DES INSTALLATIONS ÉLECTRIQUES CFO CANECO BT-HT.pdf"), file_name="Plan_CFO.pdf", mime="application/pdf", use_container_width=True)
            
            with col2:
                st.markdown("""
                <div class="course-card">
                    <div style="font-size: 3em; margin-bottom: 10px;">🏙️</div>
                    <h4 style="margin-top: 0;">Réseaux HTA-BT-EP</h4>
                    <p style="font-size:0.9em; color: #666;">Réseaux urbains et lotissements avec AutoCAD & Caneco.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN CONCEPTION DES RÉSEAUX DE DISTRIBUTION HT-BT-EP.pdf"), file_name="Plan_Reseaux.pdf", mime="application/pdf", use_container_width=True)

            with col3:
                st.markdown("""
                <div class="course-card">
                    <div style="font-size: 3em; margin-bottom: 10px;">☀️</div>
                    <h4 style="margin-top: 0;">Solaire Photovoltaïque</h4>
                    <p style="font-size:0.9em; color: #666;">Dimensionnement avancé de centrales sur PV SYST.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES SYSTEMES PHOTOVOLTAÏQUE.pdf"), file_name="Plan_Solaire.pdf", mime="application/pdf", use_container_width=True)

            st.write("")
            col4, col5, col6 = st.columns(3)

            with col4:
                st.markdown("""
                <div class="course-card">
                    <div style="font-size: 3em; margin-bottom: 10px;">💡</div>
                    <h4 style="margin-top: 0;">Éclairage (DIALux EVO)</h4>
                    <p style="font-size:0.9em; color: #666;">Étude photométrique pointue (EN 13-201 & 12464-1).</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ECLAIRAGE INTERIEUR ET EXTERIEUR 2025.pdf"), file_name="Plan_Eclairage.pdf", mime="application/pdf", use_container_width=True)

            with col5:
                st.markdown("""
                <div class="course-card">
                    <div style="font-size: 3em; margin-bottom: 10px;">📡</div>
                    <h4 style="margin-top: 0;">Télécommunications</h4>
                    <p style="font-size:0.9em; color: #666;">Infrastructures génie civil, Fibre Optique et câblage PTT.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Programme", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES RESEAUX DE TELECOMS.pdf"), file_name="Plan_Telecoms.pdf", mime="application/pdf", use_container_width=True)

        with tab_inscription:
            conn = st.connection("gsheets", type=GSheetsConnection)
            with st.container(border=True):
                st.markdown("### 📝 Dossier d'Admission")
                with st.form("formulaire_inscription"):
                    c1, c2 = st.columns(2)
                    nom_client = c1.text_input("👤 Nom complet *")
                    sexe_client = c2.selectbox("🚻 Sexe *", ["Sélectionner", "Homme", "Femme"])
                    
                    email_client = c1.text_input("📧 Email professionnel *")
                    pays_client = c2.text_input("🌍 Pays *", placeholder="Ex: Maroc, Sénégal...")
                    
                    tel_client = st.text_input("📱 WhatsApp (avec indicatif) *", placeholder="+212 6 XX XX XX XX")
                    
                    st.markdown("#### 🎯 Choix du Parcours")
                    formation_choisie = st.selectbox("Sélectionnez votre formation *", [
                        "⚡ CFO (Caneco BT-HT)", "🏙️ HTA-BT-EP", "☀️ Photovoltaïque",
                        "💡 DIALux EVO", "📡 Télécommunications", "🏢 Formation Entreprise"
                    ])
                    
                    st.caption("* Champs obligatoires")
                    soumis = st.form_submit_button("🚀 VALIDER MA CANDIDATURE", type="primary", use_container_width=True)
                    
                    if soumis:
                        if not nom_client or not email_client or not tel_client or not pays_client or sexe_client == "Sélectionner":
                            st.error("⚠️ Veuillez remplir tous les champs obligatoires.")
                        else:
                            try:
                                df_existantes = conn.read(worksheet="Inscriptions", ttl=5)
                            except:
                                df_existantes = pd.DataFrame(columns=["Date", "Nom", "Sexe", "Email", "Pays", "WhatsApp", "Formation"])

                            nouvelle = pd.DataFrame([{
                                "Date": datetime.date.today().strftime("%d/%m/%Y"),
                                "Nom": nom_client, "Sexe": sexe_client, "Email": email_client,
                                "Pays": pays_client, "WhatsApp": tel_client, "Formation": formation_choisie
                            }])

                            df_maj = pd.concat([df_existantes, nouvelle], ignore_index=True)
                            conn.update(worksheet="Inscriptions", data=df_maj)

                            st.success(f"🎉 Félicitations {nom_client}, demande enregistrée !")
                            
                            lien_wa = f"https://wa.me/212674534264?text=Bonjour FC ELEC !%0AJe confirme mon inscription pour la formation : {formation_choisie}."
                            st.markdown(f"""
                            <div style="background:#e8f5e9; padding:20px; border-radius:10px; text-align:center; border:2px solid #4CAF50;">
                                <h4 style="color:#2e7d32; margin-top:0;">Dernière Étape ⏳</h4>
                                <a href="{lien_wa}" target="_blank" style="display:inline-block; background:#25D366; color:white; padding:12px 25px; border-radius:8px; text-decoration:none; font-weight:bold;">
                                    💬 Confirmer par WhatsApp
                                </a>
                            </div>
                            """, unsafe_allow_html=True)

            with st.expander("🔐 Espace Direction FC ELEC"):
                mdp = st.text_input("Mot de passe :", type="password")
                if st.button("Déverrouiller"):
                    if mdp == "FCELEC2026": st.session_state.admin_connecte = True; st.rerun()
                    else: st.error("Accès refusé.")
                
                if st.session_state.get("admin_connecte", False):
                    st.success("Session ouverte.")
                    try:
                        df_i = conn.read(worksheet="Inscriptions", ttl=5)
                        st.dataframe(df_i, use_container_width=True)
                    except:
                        st.error("Erreur de connexion base.")

    # =========================================================
    # MODULE 2 : CARNET DE CÂBLES
    # =========================================================
    elif menu == "🔌 2. Carnet de Câbles":
        st.title("🔌 Dimensionnement des Lignes (NF C 15-100)")
        
        with st.container(border=True):
            st.markdown("### 📋 1. Projet & Localisation")
            col_p1, col_p2, col_p3 = st.columns(3)
            nom_p = col_p1.text_input("Nom du Projet", st.session_state.projet["info"]["nom"])
            st.session_state.projet["info"]["nom"] = nom_p
            nom_tab_cables = col_p2.text_input("Tableau Source", "TGBT")
            ref_c = col_p3.text_input("Désignation Circuit", "Départ Eclairage")

        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("ajout_cable"):
            st.markdown("### ⚙️ 2. Paramètres de Calcul")
            
            c1, c2, c3, c4 = st.columns(4)
            tension = c1.selectbox("Tension", ["230V Mono", "400V Tri"])
            p_w = c2.number_input("Puissance (W)", min_value=0.0, value=3500.0, step=100.0)
            longueur = c3.number_input("Longueur (m)", min_value=1.0, value=50.0, step=1.0)
            cos_phi = c4.slider("Cos φ", 0.7, 1.0, 0.85)
            
            st.divider()
            st.markdown("### 🏗️ 3. Environnement & Contraintes")
            
            c5, c6, c7, c8 = st.columns(4)
            nature = c5.selectbox("Métal Conducteur", ["Cuivre", "Aluminium"])
            type_cable = c6.selectbox("Type d'Isolant", ["U1000 R2V (PR)", "H07VU/VR (PVC)", "H07RN-F (Souple)", "XAV (Armé)", "CR1-C1 (Incendie)"])
            type_charge = c7.selectbox("Application", ["Éclairage (Max 3%)", "Prises (Max 5%)", "Force Motrice (Max 5%)", "Réseau Principal (Max 2%)"])
            methode_pose = c8.selectbox("Méthode de Pose", ["Méthode A (Encastré)", "Méthode B (Sous conduit)", "Méthode C (Fixé au mur)", "Méthode D (Enterré)", "Méthode E/F (Chemin de câbles)"])

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("⚡ Lancer le Calcul & Mémoriser", use_container_width=True, type="primary"):
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

                dict_iz = {
                    "Méthode A (Encastré)": {1.5: 14.5, 2.5: 19.5, 4: 26, 6: 34, 10: 46, 16: 61, 25: 80, 35: 99, 50: 119, 70: 151, 95: 182, 120: 210, 150: 240, 185: 273, 240: 321, 300: 367},
                    "Méthode B (Sous conduit)": {1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 151, 70: 192, 95: 232, 120: 269, 150: 309, 185: 353, 240: 415, 300: 477},
                    "Méthode C (Fixé au mur)": {1.5: 19.5, 2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 112, 35: 138, 50: 168, 70: 213, 95: 258, 120: 299, 150: 344, 185: 392, 240: 461, 300: 530},
                    "Méthode D (Enterré)": {1.5: 22, 2.5: 29, 4: 37, 6: 46, 10: 61, 16: 79, 25: 101, 35: 122, 50: 144, 70: 178, 95: 211, 120: 240, 150: 271, 185: 304, 240: 351, 300: 396},
                    "Méthode E/F (Chemin de câbles)": {1.5: 23, 2.5: 31, 4: 42, 6: 54, 10: 75, 16: 100, 25: 135, 35: 169, 50: 207, 70: 268, 95: 328, 120: 382, 150: 441, 185: 506, 240: 599, 300: 693}
                }
                
                k_al = 0.78 if "Aluminium" in nature else 1.0
                k_mono = 1.15 if "230V" in tension else 1.0
                
                S_ret_iz = 300
                for s in sections:
                    Iz_calc = dict_iz[methode_pose][s] * k_al * k_mono
                    if Iz_calc >= In:
                        S_ret_iz = s; break

                S_ret = max(S_ret_du, S_ret_iz)
                Iz_reel = dict_iz[methode_pose][S_ret] * k_al * k_mono
                du_reel_pct = (((b * rho * longueur * Ib) / S_ret) / V) * 100
                lettre_pose = methode_pose.split(" ")[1]

                st.session_state.projet["cables"].append({
                    "Tableau": nom_tab_cables, "Repère": ref_c, "Type Câble": type_cable, "Métal": nature, 
                    "Pose": lettre_pose, "Tension": tension, "P(W)": p_w, "Long.(m)": longueur,
                    "Ib(A)": round(Ib, 1), "Calibre(A)": In, "Iz(A)": round(Iz_reel, 1), "Section(mm2)": S_ret, "dU(%)": round(du_reel_pct, 2)
                })
                st.success(f"✅ Calcul validé : **{S_ret} mm²** (Iz={round(Iz_reel,1)}A) protégée par un disjoncteur **{In}A**.")

        if st.session_state.projet["cables"]:
            st.markdown("### 📑 Base de Données des Circuits")
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)
            
            def generate_pdf_cables():
                pdf = FCELEC_Report()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_fill_color(2, 136, 209)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(190, 10, f" CARNET DE CABLES - {sanitize_text(st.session_state.projet['info']['nom']).upper()}", border=0, ln=True, align="C", fill=True)
                pdf.ln(5)
                
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_fill_color(240, 240, 240)
                pdf.set_text_color(0, 0, 0)
                
                headers = ["Tab.", "Repere", "Type Cable", "L(m)", "Ib(A)", "In(A)", "Iz(A)", "Section", "dU(%)"]
                widths = [14, 26, 40, 12, 15, 15, 15, 35, 18]
                
                for i in range(len(headers)): pdf.cell(widths[i], 8, headers[i], 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_font("Helvetica", "", 8)
                for row in st.session_state.projet["cables"]:
                    pdf.cell(widths[0], 8, sanitize_text(row.get("Tableau", "TGBT"), 12), 1)
                    pdf.cell(widths[1], 8, sanitize_text(row["Repère"], 18), 1)
                    pdf.cell(widths[2], 8, sanitize_text(row.get("Type Câble", "U1000 R2V").split(" (")[0], 25), 1, 0, 'C')
                    pdf.cell(widths[3], 8, str(row["Long.(m)"]), 1, 0, 'C')
                    pdf.cell(widths[4], 8, str(row["Ib(A)"]), 1, 0, 'C')
                    
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(widths[5], 8, f"{row['Calibre(A)']}A", 1, 0, 'C')
                    pdf.set_text_color(0, 128, 0)
                    pdf.cell(widths[6], 8, f"{row.get('Iz(A)', '-')}A", 1, 0, 'C')
                    pdf.set_text_color(255, 100, 0)
                    pdf.cell(widths[7], 8, f"{row['Section(mm2)']} mm2", 1, 0, 'C')
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(widths[8], 8, str(row["dU(%)"]), 1, 1, 'C')
                return pdf.output()

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("📄 GÉNÉRER LE LIVRABLE (PDF)", type="primary", use_container_width=True):
                st.download_button("📥 Télécharger Note de Calcul", bytes(generate_pdf_cables()), f"Note_Calcul_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")
            if col_btn2.button("🗑️ Réinitialiser le Carnet", use_container_width=True):
                st.session_state.projet["cables"] = []; st.rerun()

    # =========================================================
    # MODULE 3 : ARCHITECTURE MULTI-TABLEAUX
    # =========================================================
    elif menu == "🏢 3. Bilan de Puissance":
        st.title("🏢 Bilan de Puissance Multi-Tableaux")
        
        with st.container(border=True):
            col_t1, col_t2 = st.columns([3, 1])
            nouveau_tab = col_t1.text_input("Ajouter un Tableau (ex: TGBT, TD RDC)", placeholder="Saisir le nom du tableau...")
            if col_t2.button("➕ Ajouter", use_container_width=True) and nouveau_tab:
                if nouveau_tab not in st.session_state.projet["tableaux"]:
                    st.session_state.projet["tableaux"][nouveau_tab] = []
                    st.rerun()

        if st.session_state.projet["tableaux"]:
            onglets = st.tabs(list(st.session_state.projet["tableaux"].keys()) + ["📊 SYNTHÈSE BÂTIMENT"])
            
            for i, nom_tab in enumerate(list(st.session_state.projet["tableaux"].keys())):
                with onglets[i]:
                    col_del1, col_del2 = st.columns([4,1])
                    col_del1.markdown(f"#### Configuration : {nom_tab}")
                    if col_del2.button("❌ Supprimer Tableau", key=f"del_{nom_tab}"):
                        del st.session_state.projet["tableaux"][nom_tab]; st.rerun()

                    with st.form(f"form_{i}"):
                        c1, c2, c3, c4 = st.columns([2,1,1,1])
                        c_nom = c1.text_input("Désignation du Circuit")
                        c_p = c2.number_input("Puissance (W)", min_value=0.0, value=1000.0, step=100.0)
                        
                        c_type = c3.selectbox("Famille", [
                            "Éclairage", "Prises de courant", "Chauffage", 
                            "CVC / Moteur", "Cuisson", "IRVE (Recharge VE)"
                        ])

                        if c_type in ["Éclairage", "Chauffage", "IRVE"]: ku_def = 1.0
                        elif c_type == "Prises de courant": ku_def = 0.5
                        elif c_type == "Cuisson": ku_def = 0.7
                        elif c_type == "CVC / Moteur": ku_def = 0.75
                        else: ku_def = 0.8
                            
                        c_ku = c4.number_input("Coef. Utilisation (Ku)", min_value=0.1, max_value=1.0, value=float(ku_def), step=0.05)
                        
                        if st.form_submit_button("Ajouter Ligne"):
                            st.session_state.projet["tableaux"][nom_tab].append({
                                "Circuit": c_nom, "Type": c_type, "P(W)": c_p, "Ku": c_ku, "P.Abs(W)": int(c_p * c_ku)
                            })
                            st.rerun()
                    
                    circuits = st.session_state.projet["tableaux"].get(nom_tab, [])
                    if circuits:
                        st.dataframe(pd.DataFrame(circuits), use_container_width=True)

            with onglets[-1]:
                st.markdown("### 📊 Synthèse Globale du Bâtiment")
                bilan_global = [{"Tableau": t, "Puissance Absorbée (W)": sum(c["P.Abs(W)"] for c in circs)} for t, circs in st.session_state.projet["tableaux"].items()]
                
                if bilan_global:
                    df_g = pd.DataFrame(bilan_global)
                    p_totale = df_g["Puissance Absorbée (W)"].sum()
                    ks_global = st.slider("Coefficient de Foisonnement Global Bâtiment (Ks)", 0.4, 1.0, st.session_state.projet.get("ks_global", 0.8))
                    st.session_state.projet["ks_global"] = ks_global
                    
                    p_appel = int(p_totale * ks_global)
                    kva_estime = round(p_appel / 0.8 / 1000, 1)
                    
                    # Dashboard Metrics HTML
                    st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; gap:20px; margin-top:20px; margin-bottom:20px;">
                            <div class="metric-card" style="flex:1;">
                                <div class="metric-title">Puissance Totale Installée</div>
                                <div class="metric-value">{p_totale / 1000:.1f} kW</div>
                            </div>
                            <div class="metric-card" style="flex:1; border-left-color: #4CAF50;">
                                <div class="metric-title">Puissance Active d'Appel</div>
                                <div class="metric-value" style="color:#2e7d32;">{p_appel / 1000:.1f} kW</div>
                            </div>
                            <div class="metric-card" style="flex:1; border-left-color: #FF9800;">
                                <div class="metric-title">Abonnement Estimé (S)</div>
                                <div class="metric-value" style="color:#e65100;">{kva_estime} kVA</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    def generate_pdf_bilan():
                        pdf = FCELEC_Report()
                        pdf.set_auto_page_break(auto=True, margin=15)
                        pdf.add_page()
                        pdf.set_font("Helvetica", "B", 14)
                        pdf.set_text_color(2, 136, 209)
                        pdf.cell(190, 10, f"BILAN DE PUISSANCE - {sanitize_text(st.session_state.projet['info']['nom']).upper()}", ln=True, align="C")
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

                    if st.button("📄 EXPORTER BILAN DE PUISSANCE (PDF)", type="primary", use_container_width=True):
                        st.download_button("📥 Confirmer Téléchargement", bytes(generate_pdf_bilan()), f"Bilan_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")

    # =========================================================
    # MODULE 4 : NOMENCLATURE & DEVIS
    # =========================================================
    elif menu == "💰 4. Nomenclature & Devis":
        st.title("💰 Chiffrage & Base de Prix")
        nomenclatures = []
        
        for cab in st.session_state.projet["cables"]:
            nature = cab.get("Métal", "Cuivre")
            type_c = cab.get("Type Câble", "U1000 R2V").split(" (")[0]
            nomenclatures.append({"Catégorie": "Câblage", "Désignation": f"Câble {nature} {type_c} - {cab['Section(mm2)']} mm2", "Quantité": cab["Long.(m)"], "Unité": "m", "Prix Unitaire HT": 15.0})
            nomenclatures.append({"Catégorie": "Appareillage Modulaire", "Désignation": f"Disjoncteur TGBT {cab['Calibre(A)']}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 80.0})

        for tab, circs in st.session_state.projet["tableaux"].items():
            for c in circs:
                cal_estime = 16 if c["P(W)"] <= 3500 else 20 if c["P(W)"] <= 4500 else 32
                nomenclatures.append({"Catégorie": "Appareillage Modulaire", "Désignation": f"Disjoncteur Div. {cal_estime}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 65.0})

        if not nomenclatures:
            st.info("💡 L'intelligence de chiffrage extraira les données dès que vous aurez créé des lignes de câbles ou des tableaux de distribution.")
        else:
            with st.container(border=True):
                st.markdown("### 🛒 Modification des Quantitatifs et Prix")
                df_nom = pd.DataFrame(nomenclatures)
                df_nom["Prix Unitaire HT"] = pd.to_numeric(df_nom["Prix Unitaire HT"], errors='coerce').fillna(0)
                df_nom["Quantité"] = pd.to_numeric(df_nom["Quantité"], errors='coerce').fillna(0)
                df_grouped = df_nom.groupby(["Catégorie", "Désignation", "Unité"], as_index=False).agg({"Quantité": "sum", "Prix Unitaire HT": "mean"})
                
                df_edited = st.data_editor(
                    df_grouped,
                    column_config={"Prix Unitaire HT": st.column_config.NumberColumn("Prix U. HT (MAD)", format="%.2f")},
                    hide_index=True, use_container_width=True
                )
                
                df_edited["Total HT"] = df_edited["Quantité"] * df_edited["Prix Unitaire HT"]
                total_ht = df_edited["Total HT"].sum()
                
                # Dashboard Financier
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; gap:20px; margin-top:20px;">
                        <div class="metric-card" style="flex:1; border-left-color: #757575;">
                            <div class="metric-title">TOTAL MATÉRIEL (HT)</div>
                            <div class="metric-value" style="color:#424242;">{total_ht:,.2f} MAD</div>
                        </div>
                        <div class="metric-card" style="flex:1; border-left-color: #FF4B4B;">
                            <div class="metric-title">TOTAL MATÉRIEL (TTC 20%)</div>
                            <div class="metric-value" style="color:#D32F2F;">{total_ht * 1.20:,.2f} MAD</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button("📊 EXPORTER LE DEVIS DÉTAILLÉ (.XLSX)", data=to_excel(df_edited), file_name=f"Devis_FCELEC.xlsx", type="primary", use_container_width=True)

    # =========================================================
    # MODULE 5 : OUTILS
    # =========================================================
    elif menu == "📉 5. Outils (Cos φ & IRVE)":
        st.title("🛠️ Utilitaires d'Ingénierie")
        onglets = st.tabs(["📉 Dimensionnement Condensateurs", "🚘 Infrastructure IRVE"])
        with onglets[0]:
            with st.container(border=True):
                st.markdown("### Énergie Réactive & Relèvement du Cos φ")
                p_kw = st.number_input("Puissance de l'installation (kW)", value=100.0, step=10.0)
                c1, c2 = st.columns(2)
                cos_i = c1.slider("Cos φ Initial (actuel/mesuré)", 0.5, 0.95, 0.75)
                cos_v = c2.slider("Cos φ Visé (cible distributeur)", 0.9, 1.0, 0.95)
                qc = p_kw * (math.tan(math.acos(cos_i)) - math.tan(math.acos(cos_v)))
                
                st.markdown(f"""
                    <div class="metric-card" style="margin-top:20px;">
                        <div class="metric-title">Batterie de Condensateurs requise</div>
                        <div class="metric-value">{math.ceil(qc)} kVAR</div>
                    </div>
                """, unsafe_allow_html=True)
            
        with onglets[1]:
            with st.container(border=True):
                st.markdown("### Bornes de Recharge Véhicules Électriques")
                p_b = st.selectbox("Type de borne de recharge", ["7.4 kW (32A Monophasé)", "11 kW (16A Triphasé)", "22 kW (32A Triphasé)"])
                st.info("💡 **Exigence Normative :** Le circuit spécialisé doit être protégé par un Disjoncteur Différentiel 30mA de **Type B** ou **Type A-EV**. Un câblage de 10 mm² minimum est fortement recommandé pour limiter les pertes thermiques lors des charges longues.")

    # ---------------------------------------------------------
    # PIED DE PAGE GLOBAL
    # ---------------------------------------------------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 25px; border-radius: 12px; text-align: center; border-left: 6px solid #0288d1; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="color: #01579b; margin-top: 0; font-size: 1.4em;">🎓 L'ingénierie vous passionne ?</h3>
        <p style="color: #0277bd; font-size: 1.1em; margin-bottom: 20px;">Devenez un expert technique avec <b>FC ELEC ACADEMY</b>. Formations pratiques, certifiantes et sur logiciels pro.</p>
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none; background-color: #FF4B4B; color: white; padding: 12px 25px; border-radius: 8px; font-weight: bold; transition: 0.3s; display: inline-block;">
            👉 Discuter avec un conseiller
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    foot1, foot2, foot3, foot4 = st.columns(4)
    with foot1:
        st.markdown("<h4 style='color:#01579b;'>🎓 FC ELEC</h4>", unsafe_allow_html=True)
        st.write("Ingénierie, Formation & Consulting\n📍 Rabat, Maroc")
    with foot2:
        st.markdown("<h4 style='color:#01579b;'>📱 Contact</h4>", unsafe_allow_html=True)
        st.write("WhatsApp: [+212 674-534264](https://wa.me/212674534264)\nEmail: [fcelec2.maroc@gmail.com](mailto:fcelec2.maroc@gmail.com)")
    with foot3:
        st.markdown("<h4 style='color:#01579b;'>🌐 Réseaux</h4>", unsafe_allow_html=True)
        st.markdown("[LinkedIn](https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/) | [YouTube](https://www.youtube.com/@FCELECACADEMY)")
    with foot4:
        st.markdown("<h4 style='color:#01579b;'>🚀 Nos Services</h4>", unsafe_allow_html=True)
        st.write("Études de conception\nFormations certifiantes")

    st.markdown("""
        <div style="background-color: #0e1117; padding: 15px; border-radius: 8px; text-align: center; border-top: 3px solid #0288d1; margin-top: 20px;">
            <p style="color: white; font-size: 0.85em; margin: 0; font-weight: 500;">
                © 2026 <b>FC ELEC EXPERT</b> | Plateforme d'Ingénierie Électrique.
            </p>
        </div>
    """, unsafe_allow_html=True)
