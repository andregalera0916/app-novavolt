import streamlit as st
from fpdf import FPDF
from PIL import Image
from openai import OpenAI
import io
from datetime import datetime
import tempfile
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal Novavolt", layout="wide")

# --- CONFIGURAÇÃO OPENAI ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- FUNÇÃO DA IA (CHATGPT) ---
def gerar_laudo_ia(texto_bruto):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # O modelo mais potente e estável
            messages=[
                {"role": "system", "content": "Você é um perito em vistorias imobiliárias da Novavolt. Organize as notas de forma técnica e profissional."},
                {"role": "user", "content": texto_bruto}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na conexão com ChatGPT: {e}"

# --- FUNÇÃO DE FOTOS ---
def redimensionar_foto(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    return img

# --- INTERFACE ---
st.title("🏠 Portal de Laudos Novavolt (Powered by OpenAI)")

if 'laudo_final' not in st.session_state:
    st.session_state.laudo_final = ""

col1, col2 = st.columns(2)
with col1:
    locatario = st.text_input("Nome do Locatário")
    endereco = st.text_input("Endereço do Imóvel")
with col2:
    data_v = st.date_input("Data da Vistoria", datetime.now())

notas = st.text_area("Notas da Vistoria:", height=150)

if st.button("🚀 Processar com ChatGPT"):
    if notas:
        with st.spinner("O ChatGPT está organizando seu laudo..."):
            st.session_state.laudo_final = gerar_laudo_ia(notas)
    else:
        st.warning("Digite as notas primeiro.")

laudo_editavel = st.text_area("Resultado Final:", value=st.session_state.laudo_final, height=250)

lista_fotos = st.file_uploader("Anexar Fotos", type=['jpg', 'png'], accept_multiple_files=True)

if st.button("✅ GERAR PDF"):
    if not locatario or not endereco:
        st.error("Preencha os campos obrigatórios!")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "NOVAVOLT - LAUDO TÉCNICO", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Imóvel: {endereco}\nLocatário: {locatario}\nData: {data_v}")
        pdf.ln(5)
        pdf.multi_cell(0, 5, laudo_editavel.encode('latin-1', 'replace').decode('latin-1'))
        
        pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.download_button("📥 BAIXAR PDF", data=pdf_out, file_name=f"Laudo_{locatario}.pdf")
