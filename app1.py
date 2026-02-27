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
                else:
                    st.error("Accès refusé.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.markdown("### 💾 GESTION DE PROJET")
    
    st.sidebar.info(f"📁 Projet actif : **{st.session_state.projet['info']['nom']}**")

    projet_json = json.dumps(st.session_state.projet, indent=4)
    st.sidebar.download_button("📥 Sauvegarder Projet (.json)", data=projet_json, file_name=f"{sanitize_text(st.session_state.projet['info']['nom'])}.json", mime="application/json")
    
    fichier_charge = st.sidebar.file_uploader("📂 Charger un Projet", type=['json'])
    if fichier_charge is not None:
        try:
            donnees = json.load(fichier_charge)
            if donnees != st.session_state.projet:
                st.session_state.projet = donnees
                st.sidebar.success("Projet chargé !")
                st.rerun()
        except:
            st.sidebar.error("Fichier invalide.")

    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navigation :", [
        "🔌 1. Carnet de Câbles",
        "🏢 2. Bilan de Puissance (Multi-Tab)",
        "💰 3. Nomenclature & Devis",
        "📉 4. Outils (Cos φ & IRVE)",
        "📚 5. Catalogue des Formations"
    ])

    # --- SECTION PUBLICITAIRE FC ELEC (SIDEBAR) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>🎓 FORMATIONS EXPERT</h3>", unsafe_allow_html=True)
    
    # Encart Premium pour la formation
    st.sidebar.markdown("""
        <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="color: white; font-weight: bold; margin-bottom: 5px; font-size: 1.1em;">🚀 Boostez votre carrière !</p>
            <p style="color: #e1f5fe; font-size: 0.85em; margin: 0;">Devenez un expert recherché sur le marché avec nos formations pratiques et certifiantes.</p>
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

    st.sidebar.markdown("---")

    # ---------------------------------------------------------
    # MODULE 1 : CARNET DE CÂBLES
    # ---------------------------------------------------------
    if menu == "🔌 1. Carnet de Câbles":
        st.title("🔌 Dimensionnement des Lignes")
        
        with st.container(border=True):
            st.markdown("#### 📋 Identification de la ligne")
            col_p1, col_p2, col_p3 = st.columns(3)
            nom_p = col_p1.text_input("Nom du Projet / Client", st.session_state.projet["info"]["nom"], key="proj_m1")
            st.session_state.projet["info"]["nom"] = nom_p
            nom_tab_cables = col_p2.text_input("Tableau (ex: TGBT, TD1)", "TGBT")
            ref_c = col_p3.text_input("Désignation du Circuit", "Départ Sous-sol")

            st.markdown("---")
            with st.form("ajout_cable"):
                st.markdown("#### ⚙️ Paramètres Techniques de la Ligne")
                c1, c2, c3 = st.columns(3)
                tension = c1.selectbox("Tension", ["230V", "400V"])
                p_w = c2.number_input("Puissance (W)", min_value=0.0, value=3500.0)
                longueur = c3.number_input("Longueur (m)", min_value=1.0, value=50.0)
                
                c5, c6, c7, c8 = st.columns(4)
                nature = c5.selectbox("Métal", ["Cuivre", "Aluminium"])
                
                type_cable = c6.selectbox("Type de Câble", [
                    "U1000 R2V / RO2V", 
                    "H07VU / H07VR (Fils)", 
                    "H07RN-F (Souple)", 
                    "XAV / AR2V (Armé)", 
                    "CR1-C1 (Anti-incendie)", 
                    "Câble Solaire (FG21M21)"
                ])

                type_charge = c7.selectbox("Application", [
                    "Éclairage (Max 3%)", 
                    "Prises de courant (Max 5%)",
                    "Force Motrice / Moteur (Max 5%)",
                    "Chauffage / Cuisson (Max 5%)",
                    "Ligne Principale / Abonné (Max 2%)"
                ])
                cos_phi = c8.slider("Cos φ", 0.7, 1.0, 0.85)

                if st.form_submit_button("Calculer et Ajouter au Carnet"):
                    V = 230 if "230V" in tension else 400
                    rho = 0.0225 if "Cuivre" in nature else 0.036
                    b = 2 if "230V" in tension else 1
                    
                    if "3%" in type_charge: du_max = 3.0
                    elif "2%" in type_charge: du_max = 2.0
                    else: du_max = 5.0

                    Ib = p_w / (V * cos_phi) if b == 2 else p_w / (V * math.sqrt(3) * cos_phi)
                    calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630, 800, 1000]
                    In = next((x for x in calibres if x >= Ib), 1000)
                    
                    S_calc = (b * rho * longueur * Ib) / ((du_max / 100) * V)
                    sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
                    S_ret = next((s for s in sections if s >= S_calc), 300)
                    
                    du_reel_pct = (((b * rho * longueur * Ib) / S_ret) / V) * 100

                    st.session_state.projet["cables"].append({
                        "Tableau": nom_tab_cables, "Repère": ref_c, "Type Câble": type_cable, "Métal": nature, 
                        "Tension": tension, "P(W)": p_w, "Long.(m)": longueur,
                        "Ib(A)": round(Ib, 1), "Calibre(A)": In, "Section(mm2)": S_ret, "dU(%)": round(du_reel_pct, 2)
                    })
                    st.success(f"Circuit '{ref_c}' calculé avec succès : {type_cable} {S_ret} mm² protégé par {In}A.")

        if st.session_state.projet["cables"]:
            st.markdown("### 📑 Carnet de Câbles")
            st.dataframe(pd.DataFrame(st.session_state.projet["cables"]), use_container_width=True)
            
            def generate_pdf_cables():
                pdf = FCELEC_Report()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_fill_color(230, 230, 230)
                titre = sanitize_text(st.session_state.projet['info']['nom']).upper()
                pdf.cell(190, 10, f" CARNET DE CABLES - PROJET : {titre}", border=1, ln=True, align="C", fill=True)
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_fill_color(200, 200, 200)
                
                headers = ["Tab.", "Repere", "Type Cable", "U", "L(m)", "Ib(A)", "Disj.", "Section", "dU(%)"]
                widths = [18, 25, 35, 10, 12, 15, 15, 42, 18] # Somme exacte = 190
                
                for i in range(len(headers)): 
                    pdf.cell(widths[i], 8, headers[i], 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_font("Helvetica", "", 8)
                for row in st.session_state.projet["cables"]:
                    pdf.cell(widths[0], 8, sanitize_text(row.get("Tableau", "TGBT"), 12), 1)
                    pdf.cell(widths[1], 8, sanitize_text(row["Repère"], 18), 1)
                    
                    raw_type = row.get("Type Câble", "U1000 R2V")
                    clean_type = sanitize_text(raw_type.split(" (")[0], 25) 
                    pdf.cell(widths[2], 8, clean_type, 1, 0, 'C')
                    
                    pdf.cell(widths[3], 8, str(row["Tension"])[0:3], 1, 0, 'C')
                    pdf.cell(widths[4], 8, str(row["Long.(m)"]), 1, 0, 'C')
                    pdf.cell(widths[5], 8, str(row["Ib(A)"]), 1, 0, 'C')
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(widths[6], 8, f"{row['Calibre(A)']}A", 1, 0, 'C')
                    pdf.set_text_color(255, 100, 0)
                    pdf.cell(widths[7], 8, f"{row['Section(mm2)']} mm2", 1, 0, 'C')
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(widths[8], 8, str(row["dU(%)"]), 1, 1, 'C')
                return pdf.output()

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("📄 Exporter Carnet (PDF)", type="primary"):
                st.download_button("📥 Télécharger PDF", bytes(generate_pdf_cables()), f"Cables_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")
            if col_btn2.button("🗑️ Vider le Carnet"):
                st.session_state.projet["cables"] = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 2 : ARCHITECTURE MULTI-TABLEAUX
    # ---------------------------------------------------------
    elif menu == "🏢 2. Bilan de Puissance (Multi-Tab)":
        st.title("🏢 Bilan de Puissance Global")
        
        with st.container(border=True):
            st.markdown("#### 📋 Identification du Projet")
            nom_p_m2 = st.text_input("Nom du Projet / Client", st.session_state.projet["info"]["nom"], key="proj_m2")
            st.session_state.projet["info"]["nom"] = nom_p_m2
            
            st.markdown("---")
            col_t1, col_t2 = st.columns([3, 1])
            nouveau_tab = col_t1.text_input("Ajouter un Tableau Divisionnaire (ex: TD RDC, TD Sous-sol)")
            if col_t2.button("➕ Créer le tableau", use_container_width=True) and nouveau_tab:
                if nouveau_tab not in st.session_state.projet["tableaux"]:
                    st.session_state.projet["tableaux"][nouveau_tab] = []
                    st.rerun()

        if st.session_state.projet["tableaux"]:
            onglets = st.tabs(list(st.session_state.projet["tableaux"].keys()) + ["🌍 SYNTHÈSE TGBT"])
            
            for i, nom_tab in enumerate(list(st.session_state.projet["tableaux"].keys())):
                with onglets[i]:
                    if st.button(f"❌ Supprimer le tableau '{nom_tab}'", key=f"del_{nom_tab}"):
                        del st.session_state.projet["tableaux"][nom_tab]
                        st.rerun()

                    with st.form(f"form_{i}"):
                        c1, c2, c3, c4 = st.columns([2,1,1,1])
                        c_nom = c1.text_input("Désignation Circuit (ex: Prises Salon)")
                        c_p = c2.number_input("Puissance (W)", min_value=0.0, value=1000.0)
                        
                        c_type = c3.selectbox("Type", [
                            "Éclairage", 
                            "Prises de courant", 
                            "Chauffage électrique", 
                            "Climatisation / PAC", 
                            "Force Motrice", 
                            "Cuisson", 
                            "IRVE (Recharge VE)", 
                            "Divers"
                        ])

                        if c_type in ["Éclairage", "Chauffage électrique", "IRVE (Recharge VE)"]: ku_def = 1.0
                        elif c_type == "Prises de courant": ku_def = 0.5
                        elif c_type == "Cuisson": ku_def = 0.7
                        elif c_type in ["Climatisation / PAC", "Force Motrice"]: ku_def = 0.75
                        else: ku_def = 0.8
                            
                        c_ku = c4.number_input("Ku (Utilisation)", min_value=0.1, max_value=1.0, value=float(ku_def), step=0.05)
                        
                        if st.form_submit_button("Ajouter à ce tableau"):
                            st.session_state.projet["tableaux"][nom_tab].append({
                                "Circuit": c_nom, "Type": c_type, "P(W)": c_p, "Ku": c_ku, "P.Abs(W)": int(c_p * c_ku)
                            })
                            st.rerun()
                    
                    circuits = st.session_state.projet["tableaux"].get(nom_tab, [])
                    if circuits:
                        df_tab = pd.DataFrame(circuits)
                        st.dataframe(df_tab, use_container_width=True)
                        st.metric(f"Total Absorbé ({nom_tab})", f"{df_tab['P.Abs(W)'].sum()} W")

            with onglets[-1]:
                st.markdown("### 🌍 Bilan Bâtiment (TGBT)")
                bilan_global = [{"Tableau": t, "Puissance Absorbée (W)": sum(c["P.Abs(W)"] for c in circs)} for t, circs in st.session_state.projet["tableaux"].items()]
                
                if bilan_global:
                    df_g = pd.DataFrame(bilan_global)
                    st.dataframe(df_g, use_container_width=True)
                    p_totale = df_g["Puissance Absorbée (W)"].sum()
                    
                    ks_global = st.slider("Foisonnement TGBT (Ks Global)", 0.4, 1.0, st.session_state.projet.get("ks_global", 0.8))
                    st.session_state.projet["ks_global"] = ks_global
                    
                    p_appel = int(p_totale * ks_global)
                    kva_estime = round(p_appel / 0.8 / 1000, 1)
                    
                    c1_res, c2_res = st.columns(2)
                    c1_res.success(f"**PUISSANCE ACTIVE D'APPEL : {p_appel} W**")
                    c2_res.info(f"**PUISSANCE APPARENTE (Abonnement) : {kva_estime} kVA**")

                    def generate_pdf_bilan():
                        pdf = FCELEC_Report()
                        pdf.set_auto_page_break(auto=True, margin=15)
                        pdf.add_page()
                        
                        pdf.set_font("Helvetica", "B", 14)
                        titre = sanitize_text(st.session_state.projet['info']['nom']).upper()
                        pdf.cell(190, 10, f"BILAN DE PUISSANCE MULTI-TABLEAUX - {titre}", ln=True, align="C")
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
                            pdf.cell(190, 6, f"Sous-total absorbé pour {sanitize_text(tab_name)} : {sous_total} W", border='B', ln=True, align="R")
                            pdf.ln(4)

                        pdf.ln(5)
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.set_fill_color(255, 245, 230)
                        pdf.cell(190, 10, f"PUISSANCE MAXIMALE D'APPEL (Ks={ks_global}) : {p_appel} W", border=1, ln=True, align="C", fill=True)
                        pdf.cell(190, 10, f"PUISSANCE APPARENTE ESTIMEE (Cos phi 0.8) : {kva_estime} kVA", border=1, ln=True, align="C")
                        return pdf.output()

                    if st.button("📄 Exporter Bilan Complet (PDF)", type="primary"):
                        st.download_button("📥 Télécharger Bilan PDF", bytes(generate_pdf_bilan()), f"Bilan_{sanitize_text(st.session_state.projet['info']['nom'])}.pdf")

    # ---------------------------------------------------------
    # MODULE 3 : NOMENCLATURE & DEVIS
    # ---------------------------------------------------------
    elif menu == "💰 3. Nomenclature & Devis":
        st.title("💰 Devis et Liste d'Achats")
        nomenclatures = []
        
        for cab in st.session_state.projet["cables"]:
            nature = cab.get("Métal", "Cuivre")
            type_c = cab.get("Type Câble", "U1000 R2V").split(" (")[0]
            nomenclatures.append({"Catégorie": "Câble", "Désignation": f"Câble {nature} {type_c} - {cab['Section(mm2)']} mm2", "Quantité": cab["Long.(m)"], "Unité": "m", "Prix Unitaire HT": 15.0})
            nomenclatures.append({"Catégorie": "Protection", "Désignation": f"Disjoncteur {cab['Calibre(A)']}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 80.0})

        for tab, circs in st.session_state.projet["tableaux"].items():
            for c in circs:
                cal_estime = 16 if c["P(W)"] <= 3500 else 20 if c["P(W)"] <= 4500 else 32
                nomenclatures.append({"Catégorie": "Protection", "Désignation": f"Disjoncteur Divisionnaire {cal_estime}A", "Quantité": 1, "Unité": "U", "Prix Unitaire HT": 65.0})

        if not nomenclatures:
            st.info("Saisissez des données dans les modules précédents pour générer le devis.")
        else:
            df_nom = pd.DataFrame(nomenclatures)
            df_nom["Prix Unitaire HT"] = pd.to_numeric(df_nom["Prix Unitaire HT"], errors='coerce').fillna(0)
            df_nom["Quantité"] = pd.to_numeric(df_nom["Quantité"], errors='coerce').fillna(0)
            
            df_grouped = df_nom.groupby(["Catégorie", "Désignation", "Unité"], as_index=False).agg({"Quantité": "sum", "Prix Unitaire HT": "mean"})
            
            st.write("✏️ *Astuce : Modifiez les prix unitaires. Appuyez sur Entrée, puis cliquez sur Exporter.*")
            
            df_edited = st.data_editor(
                df_grouped,
                key="editeur_devis",
                column_config={"Prix Unitaire HT": st.column_config.NumberColumn("Prix U. HT (MAD)", format="%.2f")},
                hide_index=True, use_container_width=True
            )
            
            df_edited["Total HT"] = df_edited["Quantité"] * df_edited["Prix Unitaire HT"]
            total_ht = df_edited["Total HT"].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Total Matériel (HT)", f"{total_ht:,.2f} MAD")
            c2.metric("Total Matériel (TTC 20%)", f"{total_ht * 1.20:,.2f} MAD")

            st.download_button("📊 Exporter vers Excel (.xlsx)", data=to_excel(df_edited), file_name=f"Devis_{sanitize_text(st.session_state.projet['info']['nom'])}.xlsx", type="primary")

    # ---------------------------------------------------------
    # MODULE 4 : OUTILS
    # ---------------------------------------------------------
    elif menu == "📉 4. Outils (Cos φ & IRVE)":
        onglets = st.tabs(["📉 Cos φ", "🚘 IRVE"])
        with onglets[0]:
            st.title("Compensation d'Energie Réactive")
            with st.container(border=True):
                p_kw = st.number_input("Puissance (kW)", value=100.0)
                c1, c2 = st.columns(2)
                cos_i = c1.slider("Cos φ actuel", 0.5, 0.95, 0.75)
                cos_v = c2.slider("Cos φ cible", 0.9, 1.0, 0.95)
                qc = p_kw * (math.tan(math.acos(cos_i)) - math.tan(math.acos(cos_v)))
                st.success(f"Batterie condensateurs : **{math.ceil(qc)} kVAR**")
            
        with onglets[1]:
            st.title("Mobilité Electrique (IRVE)")
            with st.container(border=True):
                p_b = st.selectbox("Puissance", ["7.4 kW (32A Mono)", "22 kW (32A Tri)"])
                st.info("Différentiel 30mA Type B. Câble : 10 mm² minimum.")

# ---------------------------------------------------------
    # MODULE 5 : CATALOGUE DES FORMATIONS ET INSCRIPTION + BASE DE DONNÉES
    # ---------------------------------------------------------
    elif menu == "📚 5. Catalogue des Formations":
        st.title("📚 FC ELEC ACADEMY : Formations & Inscription")
        st.write("Transformez votre carrière avec nos formations 100% pratiques et certifiantes basées sur des cas réels.")
        st.markdown("---")

        # Initialisation de la base de données des inscriptions dans la mémoire
        if "base_inscriptions" not in st.session_state:
            st.session_state.base_inscriptions = []

        tab_catalogue, tab_inscription = st.tabs(["📖 Catalogue & PDF", "📝 Formulaire d'Inscription"])

        # ==========================================
        # ONGLET 1 : LE CATALOGUE ET LES PDF
        # ==========================================
        with tab_catalogue:
            def charger_pdf(chemin_fichier):
                try:
                    with open(chemin_fichier, "rb") as pdf_file:
                        return pdf_file.read()
                except FileNotFoundError:
                    return b"Le catalogue PDF est en cours de mise a jour par l'equipe FC ELEC."

            # --- LIGNE 1 : 3 FORMATIONS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; height: 200px;">
                    <h4 style="color: #0288d1;">⚡ Installations Électriques CFO</h4>
                    <p style="font-size:0.9em;">Caneco BT / HT. Conception basée sur l'expérience et les normes NFCs/UTEs.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Plan (PDF)", data=charger_pdf("FORMATION EN CONCEPTION DES INSTALLATIONS ÉLECTRIQUES CFO CANECO BT-HT.pdf"), file_name="Plan_Installations_CFO_Caneco.pdf", mime="application/pdf", use_container_width=True, key="btn_cfo")
            
            with col2:
                st.markdown("""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; height: 200px;">
                    <h4 style="color: #0288d1;">🏙️ Réseaux Distribution HTA-BT-EP</h4>
                    <p style="font-size:0.9em;">AutoCAD, Caneco HT, Caneco EP et DIALux. Conception de réseaux pour lotissements.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Plan (PDF)", data=charger_pdf("FORMATION EN CONCEPTION DES RÉSEAUX DE DISTRIBUTION HT-BT-EP.pdf"), file_name="Plan_Reseaux_Distribution.pdf", mime="application/pdf", use_container_width=True, key="btn_res")

            with col3:
                st.markdown("""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; height: 200px;">
                    <h4 style="color: #0288d1;">☀️ Systèmes Solaires PV</h4>
                    <p style="font-size:0.9em;">Dimensionnement et modélisation sur PV SYST. Réseaux isolés, couplés et pompage.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Plan (PDF)", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES SYSTEMES PHOTOVOLTAÏQUE.pdf"), file_name="Plan_Solaire_PV.pdf", mime="application/pdf", use_container_width=True, key="btn_pv")

            st.write("")
            
            # --- LIGNE 2 : 2 FORMATIONS ---
            col4, col5, col6 = st.columns([1, 1, 1]) # Utilisation de 3 colonnes pour centrer ou répartir

            with col4:
                st.markdown("""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; height: 200px;">
                    <h4 style="color: #0288d1;">💡 Éclairage Int. & Extérieur</h4>
                    <p style="font-size:0.9em;">Maîtrise de DIALux EVO. Étude photométrique selon normes NF EN 13-201 & 12464-1.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Plan (PDF)", data=charger_pdf("FORMATION EN ECLAIRAGE INTERIEUR ET EXTERIEUR 2025.pdf"), file_name="Plan_Eclairage_Dialux.pdf", mime="application/pdf", use_container_width=True, key="btn_ecl")

            with col5:
                st.markdown("""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; height: 200px;">
                    <h4 style="color: #0288d1;">📡 Réseaux de Télécommunications</h4>
                    <p style="font-size:0.9em;">Infrastructures génie civil, dimensionnement des câbles PTT 88 et Fibre Optique.</p>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📄 Télécharger le Plan (PDF)", data=charger_pdf("FORMATION EN ETUDE ET CONCEPTION DES RESEAUX DE TELECOMS.pdf"), file_name="Plan_Telecoms.pdf", mime="application/pdf", use_container_width=True, key="btn_tel")

        # ==========================================
        # ONGLET 2 : LE FORMULAIRE D'INSCRIPTION ULTRA-ATTRACTIF
        # ==========================================
        with tab_inscription:
            
            # --- EN-TÊTE ATTRACTIF (DESIGN PREMIUM) ---
            st.markdown("""
            <div style="background: linear-gradient(135deg, #01579b, #0288d1); padding: 30px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.15);">
                <h2 style="margin: 0; font-size: 2.2em; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">🚀 Propulsez Votre Carrière !</h2>
                <p style="margin: 15px 0 0 0; font-size: 1.1em; opacity: 0.95;">
                    Rejoignez l'élite de l'ingénierie électrique avec <b>FC ELEC ACADEMY</b>.<br>
                    Formations 100% pratiques • Experts du terrain • Attestation reconnue
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("🔥 **Attention : Nos sessions se remplissent vite !** Remplissez ce formulaire d'inscription rapide pour bloquer votre place. Un expert vous contactera sous 24h.")
            
            # --- LE FORMULAIRE ---
            with st.form("formulaire_inscription"):
                st.markdown("### 📋 Vos Coordonnées")
                col_f1, col_f2 = st.columns(2)
                
                nom_client = col_f1.text_input("👤 Nom et Prénom *")
                sexe_client = col_f2.selectbox("🚻 Sexe *", ["Sélectionner", "Homme", "Femme"])
                
                email_client = col_f1.text_input("📧 Adresse E-mail *", placeholder="exemple@email.com")
                pays_client = col_f2.text_input("🌍 Pays de résidence *", placeholder="Ex: Maroc, France, Sénégal...")
                
                tel_client = st.text_input("📱 Numéro WhatsApp (avec indicatif) *", placeholder="+212 6 XX XX XX XX")
                
                st.markdown("### 🎯 Votre Projet")
                # MISE A JOUR DES OPTIONS DU MENU DÉROULANT ICI
                formation_choisie = st.selectbox("💡 Quelle formation va booster votre avenir ? *", [
                    "⚡ Conception des Installations Électriques CFO (Caneco BT-HT)",
                    "🏙️ Conception des Réseaux de Distribution HTA-BT-EP",
                    "☀️ Étude et Conception des Systèmes Solaires Photovoltaïques",
                    "💡 Éclairage Intérieur et Extérieur (DIALux EVO)",
                    "📡 Étude et Conception des Réseaux de Télécommunications",
                    "🏢 Formation Sur-Mesure (Entreprise)"
                ])
                
                st.markdown("<small><i>* Champs obligatoires pour valider le dossier</i></small>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True) # Espace
                
                # BOUTON D'ACTION PRINCIPAL (CALL TO ACTION)
                soumis = st.form_submit_button("✅ JE RÉSERVE MA PLACE MAINTENANT", type="primary", use_container_width=True)
                
                if soumis:
                    if not nom_client or not email_client or not tel_client or not pays_client or sexe_client == "Sélectionner":
                        st.error("⚠️ Oups ! Il manque quelques informations obligatoires pour finaliser votre réservation.")
                    else:
                        # 1. SAUVEGARDE EN BASE DE DONNÉES
                        nouvelle_inscription = {
                            "Date": datetime.date.today().strftime("%d/%m/%Y"),
                            "Nom et Prénom": nom_client,
                            "Sexe": sexe_client,
                            "E-mail": email_client,
                            "Pays": pays_client,
                            "WhatsApp": tel_client,
                            "Formation Demandée": formation_choisie
                        }
                        st.session_state.base_inscriptions.append(nouvelle_inscription)

                        # 2. MESSAGE DE SUCCÈS
                        st.success(f"🎉 Excellent choix, {nom_client} ! Votre dossier de pré-inscription est créé.")
                        
                        texte_wa = (f"Bonjour FC ELEC !%0AJe souhaite sécuriser ma place pour la prochaine session.%0A%0A"
                                    f"📋 *Mon Dossier :*%0A- *Nom :* {nom_client}%0A- *Sexe :* {sexe_client}%0A"
                                    f"- *Pays :* {pays_client}%0A- *E-mail :* {email_client}%0A- *WhatsApp :* {tel_client}%0A%0A"
                                    f"🎓 *Formation choisie :* {formation_choisie}")
                        
                        lien_wa = f"https://wa.me/212674534264?text={texte_wa}"
                        
                        st.markdown(f"""
                        <div style="background-color: #e8f5e9; padding: 25px; border-radius: 8px; text-align: center; border: 2px solid #4CAF50; margin-top: 15px;">
                            <h3 style="color: #2e7d32; margin-top:0;">Dernière étape (Très important) ⏳</h3>
                            <p style="font-size: 1.1em; color: #333;">Pour valider définitivement votre place, envoyez-nous votre confirmation sur WhatsApp en cliquant sur le bouton ci-dessous :</p>
                            <a href="{lien_wa}" target="_blank" style="display: inline-block; background-color: #25D366; color: white; padding: 15px 30px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 1.2em; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: 0.3s;">
                                💬 OUI, JE CONFIRME SUR WHATSAPP
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

            # --- ESPACE ADMINISTRATEUR SÉCURISÉ ---
            st.markdown("---")
            with st.expander("🔐 Accès Administrateur FC ELEC"):
                if "admin_connecte" not in st.session_state:
                    st.session_state.admin_connecte = False

                if not st.session_state.admin_connecte:
                    st.info("Espace sécurisé. Réservé à la direction FC ELEC.")
                    mot_de_passe = st.text_input("Mot de passe administrateur :", type="password")
                    
                    if st.button("Déverrouiller la base de données"):
                        if mot_de_passe == "FCELEC2026": 
                            st.session_state.admin_connecte = True
                            st.rerun()
                        else:
                            st.error("❌ Accès refusé.")
                
                if st.session_state.admin_connecte:
                    st.success("✅ Connexion réussie.")
                    if st.button("🔒 Verrouiller la session"):
                        st.session_state.admin_connecte = False
                        st.rerun()
                        
                    st.markdown("#### 📊 Tableau de bord des inscriptions")
                    
                    if not st.session_state.base_inscriptions:
                        st.warning("Aucun prospect enregistré pour le moment.")
                    else:
                        df_inscrits = pd.DataFrame(st.session_state.base_inscriptions)
                        st.dataframe(df_inscrits, use_container_width=True)
                        
                        output_excel = BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            df_inscrits.to_excel(writer, index=False, sheet_name='Inscriptions')
                        
                        st.download_button(
                            label="📥 TÉLÉCHARGER LE FICHIER EXCEL CLIENTS",
                            data=output_excel.getvalue(),
                            file_name=f"Base_Clients_FCELEC_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
    # ---------------------------------------------------------                        
    # PIED DE PAGE (FOOTER) - VISIBLE SUR TOUTES LES PAGES
    # ---------------------------------------------------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Bannièree Premium d'appel à l'action pour les formations
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 25px; border-radius: 10px; text-align: center; border-left: 6px solid #0288d1; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="color: #01579b; margin-top: 0; font-size: 1.4em;">🎓 Prêt à maîtriser l'ingénierie électrique ?</h3>
        <p style="color: #0277bd; font-size: 1.1em; margin-bottom: 20px;">Rejoignez <b>FC ELEC ACADEMY</b> ! Des formations 100% pratiques et certifiantes pour les professionnels et étudiants.</p>
        <a href="https://wa.me/212674534264" target="_blank" style="text-decoration: none; background-color: #FF4B4B; color: white; padding: 12px 25px; border-radius: 5px; font-weight: bold; transition: 0.3s;">
            👉 Demander le catalogue des formations
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    foot1, foot2, foot3, foot4 = st.columns(4)
    
    with foot1:
        st.markdown("#### 🎓 FC ELEC")
        st.write("Formation & Consulting en Électricité")
        st.write("Rabat, Maroc 🇲🇦")
        
    with foot2:
        st.markdown("#### 📱 Contact")
        st.write("WhatsApp : [+212 674-534264](https://wa.me/212674534264)")
        st.write("Email : [fcelec2.maroc@gmail.com](mailto:fcelec2.maroc@gmail.com)")
        
    with foot3:
        st.markdown("#### 🌐 Réseaux")
        st.markdown("[LinkedIn](https://www.linkedin.com/company/formation-et-consulting-en-electricite-fcelec/) | [YouTube](https://www.youtube.com/@FCELECACADEMY)")
        st.markdown("[Facebook](https://www.facebook.com/profile.php?id=61586577760070)")

    with foot4:
        st.markdown("#### 🚀 Services")
        st.write("Formations certifiantes")
        st.write("Accompagnement de projets")

    st.markdown(
        """
        <div style="background-color: #0e1117; padding: 10px; border-radius: 5px; text-align: center; border-top: 2px solid #FF4B4B; margin-top: 20px;">
            <p style="color: white; font-size: 0.8em; margin: 0;">
                © 2026 <b>FC ELEC EXPERT</b> | Application gratuite développée pour l'ingénierie électrique.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    if st.sidebar.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()




