import os
# FORÇA A VERSÃO ANTES DE TUDO
os.environ["GOOGLE_API_VERSION"] = "v1"

import streamlit as st
from fpdf import FPDF
from PIL import Image
import google.generativeai as genai
import io
from datetime import datetime
import tempfile

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal Novavolt", layout="wide")

# --- CONFIGURAÇÃO GEMINI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Aqui removemos o 'v1beta' que o sistema estava tentando usar
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Erro: Chave API não encontrada nos Secrets!")

# --- FUNÇÕES ---
def gerar_laudo_ia(texto_bruto):
    prompt = f"Organize tecnicamente para um laudo imobiliário: {texto_bruto}"
    try:
        # Chamada direta e simples
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def redimensionar_foto(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    return img

# --- INTERFACE ---
st.title("🏠 Portal de Laudos Novavolt")

if 'laudo_final' not in st.session_state:
    st.session_state.laudo_final = ""

col1, col2 = st.columns(2)
with col1:
    locatario = st.text_input("Locatário")
    endereco = st.text_input("Endereço")
with col2:
    data_v = st.date_input("Data", datetime.now())

notas = st.text_area("Notas da Vistoria:", height=150)

if st.button("🚀 Processar com IA"):
    if notas:
        with st.spinner("Conectando ao Google..."):
            st.session_state.laudo_final = gerar_laudo_ia(notas)
    else:
        st.warning("Digite as notas primeiro.")

laudo_editavel = st.text_area("Resultado:", value=st.session_state.laudo_final, height=250)

lista_fotos = st.file_uploader("Fotos", type=['jpg', 'png'], accept_multiple_files=True)

if st.button("✅ GERAR PDF"):
    if not locatario or not endereco:
        st.error("Preencha os dados!")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "NOVAVOLT - LAUDO TÉCNICO", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Imóvel: {endereco}\nLocatário: {locatario}\nData: {data_v}")
        pdf.ln(10)
        pdf.multi_cell(0, 5, laudo_editavel.encode('latin-1', 'replace').decode('latin-1'))
        
        pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.download_button("📥 BAIXAR PDF", data=pdf_out, file_name="laudo.pdf")
