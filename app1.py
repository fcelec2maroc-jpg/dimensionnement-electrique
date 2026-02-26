import streamlit as st
import math
import datetime
import json
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Ingénierie & Chiffrage", layout="wide", initial_sidebar_state="expanded")

# Style global
st.markdown("""
    <style>
    .reportview-container { background: #f4f6f9; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .footer-link { color: #FF4B4B; text-decoration: none; font-weight: bold; }
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
    if not isinstance(text, str): return str(text)
    clean = text.replace("φ", "phi").replace("€", "Euros").replace("é", "e").replace("è", "e").replace("à", "a").replace("É", "E")
    clean = clean.encode('latin-1', 'ignore').decode('latin-1')
    return clean[:max_len] + "..." if len(clean) > max_len else clean

# --- CLASSE PDF ---
class FCELEC_Report(FPDF):
    def header(self):
        try: self.image("logoFCELEC.png", 10, 8, 25)
        except: pass
        self.set_font("Helvetica", "B", 14)
        self.cell(30)
        self.cell(130, 8, "DOSSIER TECHNIQUE ELECTRIQUE", border=0, ln=0, align="C")
        self.set_font("Helvetica", "I", 9)
        self.cell(30, 8, f"{datetime.date.today().strftime('%d/%m/%Y')}", border=0, ln=1, align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, f"FC ELEC - WhatsApp : +212 6 74 53 42 64 | Page {self.page_no()}", 0, 0, "C")

# --- SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image("logoFCELEC.png", width=250)
            st.markdown("### 🔐 Portail Ingénierie FC ELEC")
            user = st.text_input("Identifiant")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("Authentification"):
                if "passwords" in st.secrets and user in st.secrets["passwords"] and pw == st.secrets["passwords"][user]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("Accès refusé.")
        return False
    return True

# --- CONTENU PRINCIPAL ---
if check_password():
    # 1. SIDEBAR VISUELLE
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.info(f"📁 Projet : **{st.session_state.projet['info']['nom']}**")
    
    menu = st.sidebar.radio("Navigation :", ["🔌 Carnet de Câbles", "🏢 Bilan de Puissance", "💰 Nomenclature & Devis", "📉 Outils"])

    # SECTION FORMATIONS (SIDEBAR)
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>🎓 FORMATIONS EXPERT</h3>", unsafe_allow_html=True)
    st.sidebar.markdown(f"""
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none;">
            <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🟢 WHATSAPP</div>
        </a>
        <a href="https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/" target="_blank" style="text-decoration: none;">
            <div style="background-color: #0077B5; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🔵 LINKEDIN</div>
        </a>
        <a href="https://www.facebook.com/profile.php?id=61586577760070" target="_blank" style="text-decoration: none;">
            <div style="background-color: #1877F2; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🔵 FACEBOOK</div>
        </a>
        <a href="https://www.youtube.com/@FCELECACADEMY" target="_blank" style="text-decoration: none;">
            <div style="background-color: #FF0000; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🔴 YOUTUBE</div>
        </a>
    """, unsafe_allow_html=True)

    # 2. LOGIQUE DES MODULES
    if "🔌 Carnet de Câbles" in menu:
        st.title("🔌 Dimensionnement des Lignes")
        # ... (Le code complet du Module 1 reste ici)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            nom_p = c1.text_input("Projet / Client", st.session_state.projet["info"]["nom"])
            st.session_state.projet["info"]["nom"] = nom_p
            nom_tab = c2.text_input("Tableau", "TGBT")
            ref_c = c3.text_input("Circuit", "Départ 1")
            
            with st.form("add_c"):
                col_a, col_b, col_c = st.columns(3)
                p_w = col_a.number_input("Puissance (W)", value=3500.0)
                long = col_b.number_input("Longueur (m)", value=50.0)
                tension = col_c.selectbox("U", ["230V", "400V"])
                
                col_d, col_e, col_f = st.columns(3)
                type_c = col_d.selectbox("Type", ["U1000 R2V", "H07RN-F", "H07V-U", "CR1-C1"])
                nature = col_e.selectbox("Métal", ["Cuivre", "Aluminium"])
                app = col_f.selectbox("Application", ["Eclairage (3%)", "Prises (5%)", "Moteur (5%)"])
                
                if st.form_submit_button("Calculer"):
                    # Calculs simplifiés pour démo
                    st.session_state.projet["cables"].append({"Tableau": nom_tab, "Repère": ref_c, "Type": type_c, "P(W)": p_w, "Long.(m)": long, "Section(mm2)": 2.5, "Calibre(A)": 16})
                    st.success("Ligne ajoutée.")
        
        if st.session_state.projet["cables"]:
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)

    elif "🏢 Bilan de Puissance" in menu:
        st.title("🏢 Bilan de Puissance")
        # ... (Logique Module 2 abrégée pour l'exemple, gardez votre version complète)
        st.info("Ajoutez vos tableaux divisionnaires pour calculer la puissance totale.")

    elif "💰 Nomenclature & Devis" in menu:
        st.title("💰 Devis Automatique")
        # ... (Logique Module 3)
        st.write("Modifiez vos prix et exportez vers Excel.")

    elif "📉 Outils" in menu:
        st.title("📉 Outils Ingénieur")
        # ... (Logique Module 4)

    # 3. PIED DE PAGE (FOOTER) - TOUJOURS VISIBLE
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])
    with f_col1:
        st.markdown("#### 🎓 FC ELEC - ACADEMY")
        st.write("Expertise en Ingénierie et Formation Électrique certifiante.")
        st.write("Rabat, Maroc 🇲🇦")
    with f_col2:
        st.markdown("#### 📱 Contact direct")
        st.write("WhatsApp : +212 674-534264")
        st.write("Email : fcelec.academy@gmail.com")
    with f_col3:
        st.markdown("#### 🚀 Liens Utiles")
        st.markdown("[Formations LinkedIn](https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/)")
        st.markdown("[Vidéos YouTube](https://www.youtube.com/@FCELECACADEMY)")

    st.markdown(
        """
        <div style="background-color: #0e1117; padding: 15px; border-radius: 8px; text-align: center; border-top: 3px solid #FF4B4B; margin-top: 10px;">
            <p style="color: white; font-size: 0.85em; margin: 0;">
                © 2026 <b>FC ELEC EXPERT</b> | Application Gratuite | Contact WhatsApp : <a href="https://wa.me/212674534264" class="footer-link">+212 674-534264</a>
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    if st.sidebar.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()
