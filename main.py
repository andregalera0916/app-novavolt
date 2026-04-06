import streamlit as st
from fpdf import FPDF
from PIL import Image
import google.generativeai as genai
from datetime import datetime
import tempfile
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Novavolt - Portal de Vistorias", layout="wide")

# --- CONEXÃO BLINDADA COM O GOOGLE ---
# Se o Streamlit tentar usar v1beta, esse bloco força o uso da versão estável
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Definimos o modelo de forma simples para evitar o erro 404
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro na configuração: {e}")

# --- FUNÇÃO DE PROCESSAMENTO ---
def gerar_laudo_ia(texto_bruto):
    prompt = f"Atue como perito da Novavolt. Organize estas notas de vistoria em um laudo técnico profissional: {texto_bruto}"
    try:
        # Forçamos a chamada sem stream para ser mais rápido
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Se der erro de 404 novamente, tentamos um modelo alternativo automaticamente
        try:
            alt_model = genai.GenerativeModel('gemini-1.5-pro')
            response = alt_model.generate_content(prompt)
            return response.text
        except:
            return f"Erro persistente na IA do Google: {e}. Verifique sua chave API."

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

if st.button("🚀 Processar Agora"):
    if notas:
        with st.spinner("A IA da Novavolt está trabalhando..."):
            st.session_state.laudo_final = gerar_laudo_ia(notas)
    else:
        st.warning("Preencha as notas.")

laudo_editavel = st.text_area("Laudo Editável:", value=st.session_state.laudo_final, height=250)

# Botão de PDF simplificado para não dar erro de fonte
if st.button("✅ BAIXAR PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "NOVAVOLT SOLUCOES IMOBILIARIAS", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, f"Imovel: {endereco}\nLocatario: {locatario}\nData: {data_v}")
    pdf.ln(5)
    # Removemos acentos para o PDF não travar
    texto_limpo = laudo_editavel.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, texto_limpo)
    
    pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
    st.download_button("📥 SALVAR ARQUIVO", data=pdf_out, file_name="laudo_novavolt.pdf")
