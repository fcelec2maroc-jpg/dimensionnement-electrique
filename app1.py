import streamlit as st
import math
from PIL import Image

# Configuration de la page
st.set_page_config(page_title="FC ELEC - Dimensionnement", layout="centered")

# --- AJOUT DU LOGO ---
# On charge l'image (assure-toi que le fichier s'appelle exactement logoFCELEC.png)
try:
    logo = Image.open("logoFCELEC.png")
    # On affiche le logo centré avec une largeur raisonnable
    st.image(logo, width=200)
except:
    st.warning("Logo non trouvé. Vérifiez que logoFCELEC.png est dans le dossier.")



st.title("⚡ FC ELEC :Dimensionnement Câble & Disjoncteur")
st.markdown("""
Cette application permet de déterminer la section d'un câble et le calibre du disjoncteur 
en fonction de la puissance, de la longueur et de la chute de tension admissible.
""")

# --- DONNÉES DE RÉFÉRENCE ---
SECTIONS_COMMERCIALES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
CALIBRES_DISJONCTEURS = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]

# --- INTERFACE UTILISATEUR (SIDEBAR) ---
st.sidebar.header("Paramètres d'entrée")

type_entree = st.sidebar.radio("Saisie par :", ("Puissance (W)", "Courant d'emploi Ib (A)"))

if type_entree == "Puissance (W)":
    P = st.sidebar.number_input("Puissance active (Watts)", value=3500, step=100)
    cos_phi = st.sidebar.slider("Facteur de puissance (cos φ)", 0.8, 1.0, 0.9)
else:
    Ib_input = st.sidebar.number_input("Courant d'emploi Ib (Ampères)", value=16.0, step=1.0)

tension_type = st.sidebar.selectbox("Tension (V)", ("Monophasé (230V)", "Triphasé (400V)"))
U = 230 if "230V" in tension_type else 400

longueur = st.sidebar.number_input("Longueur du câble (mètres)", value=25, min_value=1)

nature_cond = st.sidebar.selectbox("Nature du conducteur", ("Cuivre", "Aluminium"))
rho = 0.0225 if nature_cond == "Cuivre" else 0.036

delta_u_max_pct = st.sidebar.select_slider("Chute de tension max admissible (%)", options=[3, 5, 8], value=3)

# --- CALCULS ---

# 1. Calcul du Courant d'emploi (Ib)
if type_entree == "Puissance (W)":
    if U == 230:
        Ib = P / (U * cos_phi)
    else:
        # Formule triphasée : P / (U * sqrt(3) * cos_phi)
        Ib = P / (U * math.sqrt(3) * cos_phi)
else:
    Ib = Ib_input

# 2. Sélection du calibre du disjoncteur (In)
# On choisit le calibre immédiatement supérieur ou égal à Ib
In = next((x for x in CALIBRES_DISJONCTEURS if x >= Ib), CALIBRES_DISJONCTEURS[-1])

# 3. Calcul de la section minimale (S) pour la chute de tension
# Formule simplifiée : S = (rho * L * I * b) / Delta_U_volts
# b = 2 pour monophasé, b = sqrt(3) pour triphasé (entre phases)
b = 2 if U == 230 else math.sqrt(3)
delta_u_limit_volts = (delta_u_max_pct / 100) * U

# On utilise In pour le dimensionnement du câble par sécurité (NF C 15-100)
S_theo = (rho * longueur * In * b) / delta_u_limit_volts

# 4. Choix de la section commerciale supérieure
S_retenue = next((s for s in SECTIONS_COMMERCIALES if s >= S_theo), "Hors limite")

# --- AFFICHAGE DES RÉSULTATS ---

st.subheader("Résultats du dimensionnement")

col1, col2 = st.columns(2)

with col1:
    st.metric("Courant d'emploi (Ib)", f"{Ib:.2f} A")
    st.metric("Section théorique min", f"{S_theo:.2f} mm²")

with col2:
    st.metric("Calibre Disjoncteur (In)", f"{In} A")
    st.success(f"Section retenue : {S_retenue} mm²")

# 5. Calcul de la chute de tension réelle avec la section choisie
if isinstance(S_retenue, float) or isinstance(S_retenue, int):
    du_reel_v = (rho * longueur * In * b) / S_retenue
    du_reel_pct = (du_reel_v / U) * 100

    st.divider()
    st.write(f"### Vérification à {S_retenue} mm²")
    
    c1, c2 = st.columns(2)
    c1.write(f"**Chute de tension (V) :** {du_reel_v:.2f} V")
    c2.write(f"**Chute de tension (%) :** {du_reel_pct:.2f} %")
    
    if du_reel_pct <= delta_u_max_pct:
        st.info("✅ La chute de tension est conforme à votre limite.")
    else:
        st.error("⚠️ Attention : La chute de tension dépasse la limite choisie.")
else:
    st.error("La section nécessaire dépasse les standards disponibles (240 mm²).")

st.caption("Note : Ce calcul utilise la méthode simplifiée de la chute de tension selon la norme NF C 15-100.")