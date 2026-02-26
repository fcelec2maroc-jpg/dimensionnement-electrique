import streamlit as st
import math
import datetime
import json
import pandas as pd
import os
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC EXPERT - Ingénierie & Formations", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS POUR UN LOOK PROFESSIONNEL ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { background: linear-gradient(135deg, #01579b, #0288d1); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px; }
    .formation-card { background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'projet' not in st.session_state:
    st.session_state.projet = {
        "info": {"nom": "Nouveau Projet"},
        "cables": [],          
        "tableaux": {},        
        "ks_global": 0.8
    }
if "base_inscriptions" not in st.session_state:
    st.session_state.base_inscriptions = []

# --- FONCTIONS TECHNIQUES DE CALCUL ---
def calculate_sizing(p_w, tension, longueur, nature, cos_phi, du_max):
    """Calcul conforme NF C 15-100"""
    V = 230 if "230V" in tension else 400
    rho = 0.0225 if nature == "Cuivre" else 0.036
    b = 2 if V == 230 else 1 # Coefficient monophasé ou triphasé
    
    # Courant d'emploi Ib
    if V == 230:
        Ib = p_w / (V * cos_phi)
    else:
        Ib = p_w / (V * math.sqrt(3) * cos_phi)
    
    # Calibres standards disjoncteurs
    calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
    In = next((x for x in calibres if x >= Ib), 630)
    
    # Section minimale S pour la chute de tension
    du_volt_max = (du_max / 100) * V
    S_calc = (b * rho * longueur * Ib) / du_volt_max
    
    # Sections commerciales
    sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
    S_ret = next((s for s in sections if s >= S_calc), 300)
    
    # Chute de tension réelle
    du_reel_v = (b * rho * longueur * Ib) / S_ret
    du_reel_pct = (du_reel_v / V) * 100
    
    return round(Ib, 2), In, S_ret, round(du_reel_pct, 2)

# --- CLASSE PDF PROFESSIONNELLE ---
class FCELEC_Report(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 10, "FC ELEC - DOSSIER TECHNIQUE & NOTES DE CALCUL", ln=True, align="C")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 5, f"Généré le {datetime.date.today().strftime('%d/%m/%Y')}", ln=True, align="C")
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | Expertise FC ELEC Rabat | WhatsApp: +212 6 74 53 42 64", align="C")

# --- AUTHENTIFICATION ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.title("🔐 Accès Expert")
            user = st.text_input("Utilisateur")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                if user == "admin" and pw == "fcelec2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("Accès refusé.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.header("🚀 FC ELEC ENGINE")
    menu = st.sidebar.radio("Navigation", [
        "🔌 1. Dimensionnement Câbles",
        "🏢 2. Bilan de Puissance",
        "💰 3. Devis & Nomenclature",
        "📚 4. Catalogue Formations",
        "📝 5. Inscription & Admin"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : DIMENSIONNEMENT CÂBLES
    # ---------------------------------------------------------
    if menu == "🔌 1. Dimensionnement Câbles":
        st.markdown("<div class='main-header'><h1>Calcul de Lignes NF C 15-100</h1></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            ref = col1.text_input("Nom de la ligne", "Départ Armoire 1")
            p_w = col2.number_input("Puissance (Watts)", value=4500)
            longueur = col3.number_input("Longueur (m)", value=30)
            
            col4, col5, col6 = st.columns(3)
            tension = col4.selectbox("Tension", ["230V Monophasé", "400V Triphasé"])
            nature = col5.selectbox("Métal", ["Cuivre", "Aluminium"])
            du_max = col6.slider("Chute de tension max (%)", 1, 8, 3)
            
            cos_phi = st.slider("Cos φ (Facteur de puissance)", 0.7, 1.0, 0.85)
            
            if st.button("⚡ Calculer et Ajouter au carnet", type="primary", use_container_width=True):
                ib, in_c, s_r, du_r = calculate_sizing(p_w, tension, longueur, nature, cos_phi, du_max)
                st.session_state.projet["cables"].append({
                    "Repère": ref, "P(W)": p_w, "U": tension[:4], "Métal": nature,
                    "L(m)": longueur, "Ib(A)": ib, "In(A)": in_c, "S(mm²)": s_r, "dU(%)": du_r
                })
                st.success(f"Circuit {ref} calculé : {s_r} mm² retenu.")

        if st.session_state.projet["cables"]:
            st.markdown("### 📑 Carnet de Câbles")
            df = pd.DataFrame(st.session_state.projet["cables"])
            st.dataframe(df, use_container_width=True)
            if st.button("🗑️ Vider le carnet"):
                st.session_state.projet["cables"] = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 4 : CATALOGUE DES FORMATIONS (AVEC PDF RÉELS)
    # ---------------------------------------------------------
    elif menu == "📚 4. Catalogue Formations":
        st.markdown("<div class='main-header'><h1>Catalogue FC ELEC Academy 2026</h1></div>", unsafe_allow_html=True)
        
        # Liste des formations avec les noms de fichiers exacts
        formations = [
            {
                "titre": "⚡ Conception CFO (Caneco BT/HT)",
                "description": "Apprenez à concevoir des installations électriques complexes et à maîtriser Caneco.",
                "prix": "700 DH / 47 000 CFA",
                "fichier": "FORMATION EN CONCEPTION DES INSTALLATIONS ÉLECTRIQUES CFO CANECO BT-HT.pdf"
            },
            {
                "titre": "🌐 Réseaux de Distribution (HT/BT/EP)",
                "description": "Maîtrise de la distribution publique, lotissements et éclairage public.",
                "prix": "700 DH / 47 000 CFA",
                "fichier": "FORMATION EN CONCEPTION DES RÉSEAUX DE DISTRIBUTION HT-BT-EP.pdf"
            },
            {
                "titre": "☀️ Solaire Photovoltaïque (PVSYST)",
                "description": "Étude technique, dimensionnement et simulation de projets solaires.",
                "prix": "700 DH / 47 000 CFA",
                "fichier": "FORMATION EN ETUDE ET CONCEPTION DES SYSTEMES PHOTOVOLTAÏQUE.pdf"
            },
            {
                "titre": "💡 Éclairage Intérieur & Extérieur",
                "description": "Expertise en calculs photométriques avec Dialux EVO et normes d'éclairage.",
                "prix": "700 DH / 47 000 CFA",
                "fichier": "FORMATION EN ECLAIRAGE INTERIEUR ET EXTERIEUR 2025.pdf"
            },
            {
                "titre": "📞 Réseaux de Télécommunications",
                "description": "Conception d'infrastructures Télécom et réseaux fibre optique.",
                "prix": "700 DH / 47 000 CFA",
                "fichier": "FORMATION EN ETUDE ET CONCEPTION DES RESEAUX DE TELECOMS.pdf"
            }
        ]

        st.info("💡 Cliquez sur le bouton ci-dessous pour télécharger le programme détaillé en PDF.")

        for f in formations:
            with st.container():
                st.markdown(f"""
                    <div class='formation-card'>
                        <h3 style='color:#01579b; margin-top:0;'>{f['titre']}</h3>
                        <p>{f['description']}</p>
                        <p><b>💰 Investissement :</b> {f['prix']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- LECTURE DU FICHIER PDF ---
                if os.path.exists(f['fichier']):
                    with open(f['fichier'], "rb") as file_data:
                        pdf_bytes = file_data.read()
                    
                    st.download_button(
                        label=f"📄 Télécharger le programme : {f['titre']}",
                        data=pdf_bytes,
                        file_name=f['fichier'],
                        mime="application/pdf",
                        key=f['fichier']
                    )
                else:
                    st.warning(f"⚠️ Fichier programme non trouvé : {f['fichier']}")
                st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # MODULE 5 : INSCRIPTION & ADMIN
    # ---------------------------------------------------------
    elif menu == "📝 5. Inscription & Admin":
        st.markdown("<div class='main-header'><h1>Réservation de place</h1></div>", unsafe_allow_html=True)
        
        with st.form("inscription"):
            nom = st.text_input("Nom & Prénom")
            whatsapp = st.text_input("Numéro WhatsApp")
            choix = st.selectbox("Choisir la formation", ["CFO Caneco", "Réseaux Distribution", "Solaire", "Éclairage", "Télécoms"])
            
            if st.form_submit_button("Envoyer ma demande"):
                new_inscr = {"Date": str(datetime.date.today()), "Nom": nom, "WhatsApp": whatsapp, "Formation": choix}
                st.session_state.base_inscriptions.append(new_inscr)
                st.success("Inscription enregistrée !")
                
                # Lien WhatsApp
                msg = f"Bonjour FC ELEC, je souhaite m'inscrire à la formation {choix}. Nom : {nom}"
                st.markdown(f"👉 [**Cliquez ici pour finaliser sur WhatsApp**](https://wa.me/212674534264?text={msg.replace(' ', '%20')})")

        # Espace Admin (Visualisation)
        with st.expander("🔐 Visualiser les prospects (Admin uniquement)"):
            if st.session_state.base_inscriptions:
                st.table(pd.DataFrame(st.session_state.base_inscriptions))
            else: st.write("Aucun inscrit pour le moment.")

    # --- PIED DE PAGE ---
    st.markdown("---")
    st.markdown("<p style='text-align:center;'>© 2026 FC ELEC EXPERT - Ingénierie & Consulting</p>", unsafe_allow_html=True)
