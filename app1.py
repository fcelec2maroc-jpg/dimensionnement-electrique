import streamlit as st
import math
import datetime
import json
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Ingénierie & Chiffrage", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .reportview-container { background: #f4f6f9; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .footer-link { color: #FF4B4B; text-decoration: none; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA SESSION ---
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
        df.to_excel(writer, index=False, sheet_name='Chiffrage_FCELEC')
    return output.getvalue()

def sanitize_text(text, max_len=30):
    if not isinstance(text, str):
        return str(text)
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
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.line(10, 282, 200, 282)
        self.cell(0, 5, f"FC ELEC - WhatsApp : +212 6 74 53 42 64 | Page {self.page_no()}", 0, 0, "C")

# --- SÉCURITÉ ACCÈS APP ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            try: st.image("logoFCELEC.png", width=250)
            except: st.title("FC ELEC")
            st.markdown("### 🔐 Portail Ingénierie FC ELEC")
            user = st.text_input("Identifiant")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("Authentification"):
                if "passwords" in st.secrets and user in st.secrets["passwords"] and pw == st.secrets["passwords"][user]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Accès refusé.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.markdown("### 💾 GESTION DE PROJET")
    st.sidebar.info(f"📁 Projet : **{st.session_state.projet['info']['nom']}**")
    
    menu = st.sidebar.radio("Navigation :", [
        "🔌 1. Carnet de Câbles",
        "🏢 2. Bilan de Puissance",
        "💰 3. Nomenclature & Devis",
        "📉 4. Outils (Cos φ & IRVE)",
        "📚 5. Catalogue & Inscription"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : CARNET DE CÂBLES
    # ---------------------------------------------------------
    if menu == "🔌 1. Carnet de Câbles":
        st.title("🔌 Dimensionnement des Lignes")
        with st.form("ajout_cable"):
            c1, c2, c3 = st.columns(3)
            tension = c1.selectbox("Tension", ["230V", "400V"])
            p_w = c2.number_input("Puissance (W)", min_value=0.0, value=3500.0)
            longueur = c3.number_input("Longueur (m)", min_value=1.0, value=50.0)
            
            if st.form_submit_button("Calculer et Ajouter"):
                # Calcul simplifié NF C 15-100
                V = 230 if "230V" in tension else 400
                rho = 0.0225 
                b = 2 if "230V" in tension else 1
                Ib = p_w / (V * 0.85) if b == 2 else p_w / (V * 1.732 * 0.85)
                S_calc = (b * rho * longueur * Ib) / (0.05 * V)
                sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
                S_ret = next((s for s in sections if s >= S_calc), 120)
                
                st.session_state.projet["cables"].append({
                    "Repère": f"Ligne {len(st.session_state.projet['cables'])+1}",
                    "Tension": tension, "P(W)": p_w, "Long.(m)": longueur,
                    "Ib(A)": round(Ib, 1), "Section(mm2)": S_ret
                })
                st.success(f"Câble ajouté : {S_ret} mm²")
        
        if st.session_state.projet["cables"]:
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)

    # ---------------------------------------------------------
    # MODULE 5 : CATALOGUE & INSCRIPTION (AVEC CONNEXION GOOGLE)
    # ---------------------------------------------------------
    elif menu == "📚 5. Catalogue & Inscription":
        st.title("📚 FC ELEC ACADEMY")
        tab_cat, tab_ins = st.tabs(["📖 Nos Formations", "📝 Inscription Directe"])

        with tab_cat:
            st.markdown("### Téléchargez nos programmes détaillés")
            c1, c2 = st.columns(2)
            with c1:
                st.info("⚡ Études Électriques & NF C 15-100")
                st.button("📄 Plan Études.pdf", disabled=True) # Remplacer par download_button si fichier présent
            with c2:
                st.info("☀️ Solaire Photovoltaïque")
                st.button("📄 Plan Solaire.pdf", disabled=True)

        with tab_ins:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px;">
                <h2 style="margin: 0;">🚀 Réservez votre place !</h2>
                <p>Rejoignez nos prochaines sessions pratiques.</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("form_inscription"):
                col_a, col_b = st.columns(2)
                nom_client = col_a.text_input("👤 Nom et Prénom *")
                sexe_client = col_b.selectbox("🚻 Sexe *", ["Homme", "Femme"])
                email_client = col_a.text_input("📧 E-mail *")
                tel_client = col_b.text_input("📱 WhatsApp *", placeholder="+212...")
                formation = st.selectbox("🎓 Formation souhaitée", ["Études Électriques", "Solaire PV", "Électricité Industrielle", "IRVE"])
                
                soumis = st.form_submit_button("✅ ENVOYER MON INSCRIPTION", type="primary", use_container_width=True)

            if soumis:
                if not nom_client or not email_client or not tel_client:
                    st.error("Veuillez remplir les champs obligatoires.")
                else:
                    try:
                        # --- CONNEXION GOOGLE SHEETS VIA SECRETS ---
                        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                        import json
                        creds_dict = json.loads(st.secrets["google_credentials"])
                        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                        client = gspread.authorize(creds)
                        
                        # Ouverture du fichier (Vérifiez que le nom est EXACT sur votre Drive)
                        feuille = client.open("Base_Inscriptions_FCELEC").sheet1
                        
                        # Préparation des données
                        nouvelle_ligne = [
                            datetime.date.today().strftime("%d/%m/%Y"),
                            nom_client, sexe_client, email_client, tel_client, formation
                        ]
                        feuille.append_row(nouvelle_ligne)

                        # Enregistrement local aussi
                        st.session_state.base_inscriptions.append({"Nom": nom_client, "Formation": formation})

                        st.success(f"✅ Merci {nom_client} ! Inscription réussie.")
                        
                        # Lien WhatsApp
                        msg_wa = f"Bonjour, je m'inscris pour la formation {formation}. Nom: {nom_client}"
                        link_wa = f"https://wa.me/212674534264?text={msg_wa.replace(' ', '%20')}"
                        st.markdown(f'<a href="{link_wa}" target="_blank" style="display: block; background: #25D366; color: white; text-align: center; padding: 15px; border-radius: 8px; text-decoration: none; font-weight: bold;">💬 CONFIRMER SUR WHATSAPP</a>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Erreur de connexion Google : {e}")

        # --- ESPACE ADMIN SÉCURISÉ ---
        st.markdown("---")
        with st.expander("🔐 Espace Administrateur"):
            pwd_admin = st.text_input("Code Secret Admin", type="password")
            if pwd_admin == "FCELEC2026":
                st.success("Accès autorisé")
                if st.session_state.base_inscriptions:
                    st.table(st.session_state.base_inscriptions)
                else:
                    st.write("Aucun inscrit aujourd'hui.")

    # --- FOOTER ---
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>© 2026 FC ELEC ACADEMY - Rabat, Maroc</p>", unsafe_allow_html=True)

    if st.sidebar.button("🔴 DÉCONNEXION"):
        st.session_state.clear()
        st.rerun()
