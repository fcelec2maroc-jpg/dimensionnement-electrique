import streamlit as st
import math
import datetime
import json
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Ingénierie & Chiffrage", layout="wide", initial_sidebar_state="expanded")

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

if "base_inscriptions" not in st.session_state:
    st.session_state.base_inscriptions = []

# --- FONCTIONS UTILITAIRES ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inscriptions_FCELEC')
    return output.getvalue()

def sanitize_text(text, max_len=30):
    """Blindage contre les crashs PDF"""
    if not isinstance(text, str): return str(text)
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
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.line(10, 282, 200, 282)
        self.cell(0, 5, f"FC ELEC - WhatsApp : +212 6 74 53 42 64 | Page {self.page_no()}", 0, 0, "C")

# --- SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            try: st.image("logoFCELEC.png", width=250)
            except: pass
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

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.markdown("### 💾 GESTION DE PROJET")
    st.sidebar.info(f"📁 Projet actif : **{st.session_state.projet['info']['nom']}**")

    menu = st.sidebar.radio("Navigation :", [
        "🔌 1. Carnet de Câbles",
        "🏢 2. Bilan de Puissance (Multi-Tab)",
        "💰 3. Nomenclature & Devis",
        "📉 4. Outils (Cos φ & IRVE)",
        "📚 5. Catalogue des Formations"
    ])

    # Liens Sociaux Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>🎓 FORMATIONS</h3>", unsafe_allow_html=True)
    st.sidebar.markdown(f"""
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none;">
            <div style="background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🟢 WHATSAPP</div>
        </a>
        <a href="https://www.youtube.com/@FCELECACADEMY" target="_blank" style="text-decoration: none;">
            <div style="background-color: #FF0000; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 8px; font-weight: bold;">🔴 YOUTUBE</div>
        </a>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # MODULE 1 : CARNET DE CÂBLES
    # ---------------------------------------------------------
    if menu == "🔌 1. Carnet de Câbles":
        st.title("🔌 Dimensionnement des Lignes")
        with st.container(border=True):
            st.session_state.projet["info"]["nom"] = st.text_input("Nom du Projet", st.session_state.projet["info"]["nom"])
            with st.form("ajout_cable"):
                c1, c2, c3 = st.columns(3)
                tension = c1.selectbox("Tension", ["230V", "400V"])
                p_w = c2.number_input("Puissance (W)", min_value=0.0, value=3500.0)
                longueur = c3.number_input("Longueur (m)", min_value=1.0, value=50.0)
                if st.form_submit_button("Calculer et Ajouter"):
                    V = 230 if "230V" in tension else 400
                    Ib = p_w / (V * 0.85) if "230V" in tension else p_w / (V * 1.732 * 0.85)
                    S_calc = (2 * 0.0225 * longueur * Ib) / (0.05 * V)
                    sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
                    S_ret = next((s for s in sections if s >= S_calc), 120)
                    st.session_state.projet["cables"].append({
                        "Tableau": "TGBT", "Repère": f"L{len(st.session_state.projet['cables'])+1}",
                        "Tension": tension, "P(W)": p_w, "Long.(m)": longueur,
                        "Ib(A)": round(Ib, 1), "Section(mm2)": S_ret, "dU(%)": 5.0
                    })
        if st.session_state.projet["cables"]:
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE
    # ---------------------------------------------------------
    elif menu == "🏢 2. Bilan de Puissance (Multi-Tab)":
        st.title("🏢 Bilan de Puissance Global")
        nouveau_tab = st.text_input("Ajouter un Tableau (ex: TD ÉTAGE)")
        if st.button("➕ Créer") and nouveau_tab:
            st.session_state.projet["tableaux"][nouveau_tab] = []
        
        if st.session_state.projet["tableaux"]:
            tabs = st.tabs(list(st.session_state.projet["tableaux"].keys()))
            for i, nom in enumerate(st.session_state.projet["tableaux"].keys()):
                with tabs[i]:
                    with st.form(f"f_{nom}"):
                        circ = st.text_input("Circuit")
                        pw = st.number_input("Puissance (W)", value=1000)
                        if st.form_submit_button("Ajouter"):
                            st.session_state.projet["tableaux"][nom].append({"Circuit": circ, "P.Abs(W)": pw})
                    st.write(pd.DataFrame(st.session_state.projet["tableaux"][nom]))

    # ---------------------------------------------------------
    # MODULE 3 : NOMENCLATURE & DEVIS
    # ---------------------------------------------------------
    elif menu == "💰 3. Nomenclature & Devis":
        st.title("💰 Devis Matériel")
        st.info("Ce module regroupe vos câbles et protections calculés.")
        # Logique de chiffrage ici...
        st.warning("Ajoutez des câbles en Module 1 pour voir le devis.")

    # ---------------------------------------------------------
    # MODULE 5 : CATALOGUE ET INSCRIPTION (PREMIUM)
    # ---------------------------------------------------------
    elif menu == "📚 5. Catalogue des Formations":
        st.title("📚 FC ELEC ACADEMY")
        tab_cat, tab_ins = st.tabs(["📖 Catalogue", "📝 Inscription"])

        with tab_cat:
            st.info("⚡ Études Électriques | ☀️ Solaire PV | ⚙️ Industrie | 🚘 IRVE")

        with tab_ins:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 30px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px;">
                <h2 style="margin: 0;">🚀 Propulsez Votre Carrière !</h2>
                <p>Inscrivez-vous pour bloquer votre place.</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_ins"):
                nom = st.text_input("Nom et Prénom *")
                email = st.text_input("E-mail *")
                tel = st.text_input("WhatsApp *")
                formation = st.selectbox("Formation", ["Études Électriques", "Solaire PV", "Industrie", "IRVE"])
                soumis = st.form_submit_button("✅ JE RÉSERVE MA PLACE MAINTENANT", type="primary", use_container_width=True)

            if soumis:
                if nom and email and tel:
                    st.session_state.base_inscriptions.append({
                        "Date": datetime.date.today().strftime("%d/%m/%Y"),
                        "Nom": nom, "Email": email, "WhatsApp": tel, "Formation": formation
                    })
                    st.success("🎉 Inscription réussie !")
                    msg = f"Bonjour, je m'inscris pour {formation}. Nom: {nom}"
                    link = f"https://wa.me/212674534264?text={msg.replace(' ', '%20')}"
                    st.markdown(f'<a href="{link}" target="_blank" style="display:block; background:#25D366; color:white; text-align:center; padding:15px; border-radius:8px; text-decoration:none; font-weight:bold;">💬 CONFIRMER SUR WHATSAPP</a>', unsafe_allow_html=True)

        # --- ESPACE ADMINISTRATEUR SÉCURISÉ (EXCEL) ---
        st.markdown("---")
        with st.expander("🔐 Accès Administrateur FC ELEC"):
            pwd = st.text_input("Mot de passe", type="password")
            if pwd == "FCELEC2026":
                st.markdown("#### 📋 Base de données des prospects")
                if st.session_state.base_inscriptions:
                    df_res = pd.DataFrame(st.session_state.base_inscriptions)
                    st.dataframe(df_res, use_container_width=True)
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE FICHIER EXCEL CLIENTS",
                        data=to_excel(df_res),
                        file_name=f"Inscriptions_FCELEC_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
                else: st.warning("Aucune inscription pour le moment.")

    # --- FOOTER ---
    st.markdown("<br><hr><div style='text-align:center; color:gray;'>© 2026 FC ELEC EXPERT | Rabat, Maroc 🇲🇦</div>", unsafe_allow_html=True)
    if st.sidebar.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()
