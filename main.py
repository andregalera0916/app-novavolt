import streamlit as st
from fpdf import FPDF
from PIL import Image
import google.generativeai as genai
import io
from datetime import datetime
import tempfile
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal de Vistorias Novavolt", layout="wide")

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button {
        background-color: #000080; 
        color: white;
        border-radius: 5px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #0000cd; border: 1px solid white; }
    h1, h2, h3 { color: #000080; font-family: 'Arial'; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; color: #000080; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO GEMINI ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={"temperature": 0.7}
)

# --- CLASSE PARA GERAÇÃO DO PDF ---
class VistoriaPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 128)
        self.cell(0, 10, 'NOVAVOLT SOLUÇÕES IMOBILIÁRIAS', ln=True, align='L')
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, 'LAUDO DE VISTORIA TÉCNICA - MODELO 2', ln=True, align='L')
        self.set_draw_color(0, 0, 128)
        self.line(10, 26, 200, 26)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Novavolt Soluções Imobiliárias - Página {self.page_no()}', align='C')

    def section_title(self, label):
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(0, 0, 128)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {label.upper()}", ln=True, fill=True)
        self.ln(3)

# --- FUNÇÕES DE PROCESSAMENTO ---
def gerar_laudo_ia(texto_bruto):
    prompt = f"Organize estas notas de vistoria no padrão Novavolt: {texto_bruto}"
    try:
        response = model.generate_content(prompt, stream=False)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def redimensionar_foto(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    return img

# --- INTERFACE DO USUÁRIO ---
st.title("🏠 Portal de Laudos Novavolt")

tab1, tab2, tab3 = st.tabs(["📝 Dados e Texto", "📸 Fotos do Imóvel", "📄 Gerar PDF"])

if 'laudo_final' not in st.session_state:
    st.session_state.laudo_final = ""

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        data_v = st.date_input("Data da Vistoria", datetime.now())
        locatario = st.text_input("Nome do Locatário")
        locador = st.text_input("Nome do Locador")
    with col2:
        endereco = st.text_input("Endereço do Imóvel")
        mobilia = st.selectbox("Status Mobília", ["Sem mobília", "Semi-mobiliado", "Mobiliado"])

    st.divider()
    notas = st.text_area("Indique os cômodos e as condições:", height=200)
    
    if st.button("🚀 Processar Laudo"):
        if notas:
            with st.spinner("Analisando..."):
                st.session_state.laudo_final = gerar_laudo_ia(notas)
        else:
            st.warning("Insira as notas.")

    laudo_editavel = st.text_area("Resultado:", value=st.session_state.laudo_final, height=300)

with tab2:
    lista_fotos = st.file_uploader("Selecione fotos", type=['jpg', 'png'], accept_multiple_files=True)

with tab3:
    if st.button("✅ GERAR PDF"):
        if not locatario or not endereco:
            st.error("Preencha Locatário e Endereço.")
        else:
            with st.spinner("Gerando..."):
                pdf = VistoriaPDF()
                pdf.add_page()
                pdf.section_title("INFORMAÇÕES GERAIS")
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"IMÓVEL: {endereco.upper()}", ln=True)
                pdf.cell(0, 6, f"LOCATÁRIO: {locatario}", ln=True)
                pdf.ln(5)
                
                pdf.section_title("DETALHAMENTO")
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 5, laudo_editavel.encode('latin-1', 'replace').decode('latin-1'))
                
                if lista_fotos:
                    pdf.add_page()
                    pdf.section_title("ANEXO FOTOGRÁFICO")
                    x_pos, y_pos = 10, pdf.get_y() + 5
                    for i, foto in enumerate(lista_fotos):
                        img_p = redimensionar_foto(foto)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            img_p.save(tmp.name, format="JPEG", quality=75)
                            if y_pos + 46 > 270:
                                pdf.add_page()
                                y_pos = 25
                            pdf.image(tmp.name, x=x_pos, y=y_pos, w=62, h=46)
                            if (i + 1) % 3 == 0:
                                x_pos = 10
                                y_pos += 56
                            else:
                                x_pos += 66
                            os.unlink(tmp.name)

                pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button("📥 BAIXAR LAUDO", data=pdf_out, file_name="laudo.pdf")
