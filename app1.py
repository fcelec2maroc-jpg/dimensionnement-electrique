import streamlit as st
import math
import datetime
import json
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Ingénierie & Chiffrage", layout="wide", initial_sidebar_state="expanded")

# CSS Personnalisé
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #01579b; font-weight: bold; text-align: center; }
    .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DES DONNÉES ---
if 'projet' not in st.session_state:
    st.session_state.projet = {
        "info": {"nom": "Nouveau Projet"},
        "cables": [],          
        "tableaux": {},        
        "ks_global": 0.8
    }

if "base_inscriptions" not in st.session_state:
    st.session_state.base_inscriptions = []

# --- OUTILS & CALCULS ---
def calculate_cable(p_w, tension, longueur, nature, cos_phi, du_max):
    """Logique de calcul NF C 15-100"""
    V = 230 if "230V" in tension else 400
    rho = 0.0225 if nature == "Cuivre" else 0.036
    # b = 2 pour monophasé, b = 1 pour triphasé (équilibré)
    b = 2 if V == 230 else 1
    
    # Courant d'emploi Ib
    if V == 230:
        Ib = p_w / (V * cos_phi)
    else:
        Ib = p_w / (V * math.sqrt(3) * cos_phi)
        
    # Calibre Disjoncteur In (Standard)
    calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
    In = next((x for x in calibres if x >= Ib), 630)
    
    # Section théorique S (mm²) pour la chute de tension
    # Formule : dU = (b * rho * L * Ib) / S
    # Donc S = (b * rho * L * Ib) / (dU_admissible)
    du_volt_max = (du_max / 100) * V
    S_calc = (b * rho * longueur * Ib) / du_volt_max
    
    # Section commerciale
    sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
    S_ret = next((s for s in sections if s >= S_calc), 300)
    
    # Chute de tension réelle
    du_reel_v = (b * rho * longueur * Ib) / S_ret
    du_reel_pct = (du_reel_v / V) * 100
    
    return round(Ib, 2), In, S_ret, round(du_reel_pct, 2)

# --- CLASSE PDF ---
class FCELEC_Report(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "FC ELEC - DOSSIER TECHNIQUE", ln=True, align="C")
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | WhatsApp: +212 6 74 53 42 64", align="C")

# --- AUTHENTIFICATION SIMPLIFIÉE (Pour test) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Accès FC ELEC")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            if user == "admin" and pw == "fcelec2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
        return False
    return True

if check_password():
    # --- SIDEBAR ---
    st.sidebar.title("⚡ FC ELEC PRO")
    menu = st.sidebar.radio("Navigation", [
        "🔌 1. Carnet de Câbles",
        "🏢 2. Bilan de Puissance",
        "💰 3. Devis & Matériel",
        "📚 4. Inscription Formation"
    ])

    # --- MODULE 1 : CARNET DE CÂBLES ---
    if menu == "🔌 1. Carnet de Câbles":
        st.title("🔌 Dimensionnement des Liaisons")
        
        with st.expander("➕ Ajouter un nouveau circuit", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ref = st.text_input("Désignation du circuit", "Départ Principal")
                p_w = st.number_input("Puissance (Watts)", value=5000)
            with col2:
                tension = st.selectbox("Tension", ["230V Monophasé", "400V Triphasé"])
                longueur = st.number_input("Longueur (mètres)", value=25)
            with col3:
                nature = st.selectbox("Nature du métal", ["Cuivre", "Aluminium"])
                du_limite = st.slider("Chute de tension max (%)", 1, 10, 3)
            
            cos_phi = st.slider("Facteur de puissance (Cos φ)", 0.7, 1.0, 0.85)
            
            if st.button("Calculer et Enregistrer"):
                ib, in_calc, s_ret, du_r = calculate_cable(p_w, tension, longueur, nature, cos_phi, du_limite)
                st.session_state.projet["cables"].append({
                    "Circuit": ref, "P(W)": p_w, "U": tension[:4], "L(m)": longueur,
                    "Ib(A)": ib, "In(A)": in_calc, "S(mm²)": s_ret, "dU(%)": du_r
                })
                st.success("Circuit ajouté !")

        if st.session_state.projet["cables"]:
            df_cables = pd.DataFrame(st.session_state.projet["cables"])
            st.table(df_cables)
            
            if st.button("🗑️ Vider la liste"):
                st.session_state.projet["cables"] = []
                st.rerun()

    # --- MODULE 2 : BILAN DE PUISSANCE ---
    elif menu == "🏢 2. Bilan de Puissance":
        st.title("🏢 Bilan de Puissance Multi-Tableaux")
        # Logique de gestion de tableaux simplifiée pour l'exemple
        tab_name = st.text_input("Nom du Tableau", "TGBT")
        p_inst = st.number_input("Puissance Installée (W)", 0)
        ku = st.slider("Coefficient d'utilisation (Ku)", 0.1, 1.0, 0.8)
        
        if st.button("Ajouter au bilan"):
            st.session_state.projet["tableaux"][tab_name] = p_inst * ku
            st.rerun()
            
        if st.session_state.projet["tableaux"]:
            st.write(st.session_state.projet["tableaux"])
            total = sum(st.session_state.projet["tableaux"].values())
            st.metric("Puissance Totale Appelée", f"{total/1000:.2f} kVA")

    # --- MODULE 4 : FORMATION ---
    elif menu == "📚 4. Inscription Formation":
        st.title("📚 FC ELEC ACADEMY")
        st.markdown("""
        <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #2196f3;">
            <h3>Devenez un expert en Ingénierie Électrique</h3>
            <p>Inscrivez-vous à nos sessions pratiques sur Caneco BT, AutoCAD et la NF C 15-100.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("inscription"):
            nom = st.text_input("Nom Complet")
            email = st.text_input("Email")
            tel = st.text_input("WhatsApp")
            formation = st.selectbox("Formation choisie", ["Études Électriques", "Solaire PV", "Industrie"])
            if st.form_submit_button("Réserver ma place"):
                st.balloons()
                st.success(f"Merci {nom}, nous vous contacterons sur {tel} !")

    # Footer constant
    st.sidebar.markdown("---")
    st.sidebar.info("© 2026 FC ELEC - Rabat, Maroc")
