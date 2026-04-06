import streamlit as st
from fpdf import FPDF
from PIL import Image
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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
# Cole sua chave aqui ou configure nos Secrets do Streamlit/Replit
import streamlit as st
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')
# --- CLASSE PARA GERAÇÃO DO PDF ---
class VistoriaPDF(FPDF):
    def header(self):
        # Cabeçalho Profissional Novavolt
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
    prompt = f"""
    Você é o Especialista em Laudos Técnicos da Novavolt.
    Sua tarefa é organizar as notas de vistoria no padrão "MODELO 2".
    
    DIRETRIZES:
    1. Identifique os AMBIENTES citados no texto (Ex: Cozinha, Sala, Suíte 1).
    2. Para cada ambiente, liste os itens usando EXATAMENTE este formato:
       [Número]. [Item] | Material: [Material]; Cor: [Cor]; Estado: [ESTADO EM MAIÚSCULAS]; Descrição: [Texto Técnico].
    3. Use apenas: NOVO, BOM, REGULAR, NÃO TESTADO ou RUIM.
    4. Mantenha uma linguagem técnica (ex: 'Sinais de oxidação', 'Desgaste por uso', 'Pintura íntegra').
    
    NOTAS BRUTAS:
    {texto_bruto}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na conexão com a IA: {e}"

def redimensionar_foto(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # Redução para garantir performance com 500 fotos
    img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
    return img

# --- INTERFACE DO USUÁRIO ---
st.title("🏠 Portal de Laudos Novavolt")

tab1, tab2, tab3 = st.tabs(["📝 Dados e Texto", "📸 Fotos do Imóvel", "📄 Gerar PDF"])

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
    st.subheader("Entrada de Dados da Vistoria")
    notas = st.text_area("Indique os cômodos e as condições (Ex: 'Cozinha: pia inox com riscos... Quarto 1: pintura nova...')", height=250)
    
    if st.button("🚀 Processar e Organizar Laudo"):
        if notas:
            with st.spinner("IA Novavolt analisando ambientes..."):
                resultado = gerar_laudo_ia(notas)
                st.session_state.laudo_final = resultado
        else:
            st.warning("Por favor, insira as notas da vistoria.")

    laudo_editavel = st.text_area("Resultado Final (Modelo 2):", value=st.session_state.get('laudo_final', ""), height=400)

with tab2:
    st.subheader("Anexo de Fotos")
    lista_fotos = st.file_uploader("Selecione até 500 fotos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    if lista_fotos:
        st.success(f"{len(lista_fotos)} fotos prontas para o laudo.")

with tab3:
    st.subheader("Finalização do Arquivo")
    if st.button("✅ GERAR E BAIXAR LAUDO PDF"):
        if not locatario or not endereco:
            st.error("Preencha os campos obrigatórios (Locatário e Endereço).")
        else:
            with st.spinner("Construindo PDF com grade de fotos..."):
                pdf = VistoriaPDF()
                pdf.set_auto_page_break(auto=True, margin=20)
                pdf.add_page()
                
                # Dados Gerais
                pdf.section_title("INFORMAÇÕES GERAIS")
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0,0,0)
                pdf.cell(0, 6, f"IMÓVEL: {endereco.upper()}", ln=True)
                pdf.cell(0, 6, f"LOCATÁRIO: {locatario} | LOCADOR: {locador}", ln=True)
                pdf.cell(0, 6, f"DATA: {data_v.strftime('%d/%m/%Y')} | STATUS: {mobilia.upper()}", ln=True)
                pdf.ln(5)
                
                # Texto Técnico Gerado pela IA
                pdf.section_title("DETALHAMENTO DOS AMBIENTES")
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 5, laudo_editavel)
                
                # Anexo Fotográfico (3 por linha)
                if lista_fotos:
                    pdf.add_page()
                    pdf.section_title("ANEXO FOTOGRÁFICO")
                    
                    x_pos = 10
                    y_pos = pdf.get_y() + 5
                    largura_img = 62
                    altura_img = 46
                    
                    for i, foto in enumerate(lista_fotos):
                        img_processada = redimensionar_foto(foto)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            img_processada.save(tmp.name, format="JPEG", quality=75)
                            
                            # Quebra de página se não houver espaço para a linha
                            if y_pos + altura_img > 270:
                                pdf.add_page()
                                y_pos = 25
                            
                            pdf.image(tmp.name, x=x_pos, y=y_pos, w=largura_img, h=altura_img)
                            pdf.set_xy(x_pos, y_pos + altura_img + 1)
                            pdf.set_font('Arial', '', 7)
                            pdf.cell(largura_img, 4, f"FOTO {i+1:02d}", align='C')
                            
                            # Organização da Grade
                            if (i + 1) % 3 == 0:
                                x_pos = 10
                                y_pos += altura_img + 12
                            else:
                                x_pos += largura_img + 4
                            
                            os.unlink(tmp.name)

                # Output
                pdf_output = pdf.output(dest='S').encode('latin1', 'ignore')
                st.download_button("📥 BAIXAR LAUDO FINALIZADO", data=pdf_output, file_name=f"Laudo_Novavolt_{locatario}.pdf", mime="application/pdf")
