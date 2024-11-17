import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import io

st.set_page_config(
    page_title="Calculadora de Orçamentos",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': 'https://docs.streamlit.io',
        'About': "# Programação Engenharia Civil"
    }
)

# Cabeçalho e imagem do site
with st.container():
    st.image("tech.jpg", use_column_width=True)
    
st.title("Bem-vindo/a!")
st.header("Calculadora de Orçamentos - Eng. Civil 2024")

# Customização do estilo
st.markdown(
    """
    <style>
        .css-1m8jjsw edgvbvh3 {
        background-color: #135fa6; /* COR FUNDO */
        color: white; /* COR TEXTO */
    }
    </style>
    """,
    unsafe_allow_html=True
)  

# Função para carregar a planilha
def carregar_planilha():
    uploaded_file = st.file_uploader("Carregue sua planilha aqui:", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            st.write("Produtos carregados:", df)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar a planilha: {e}")
    else:
        st.warning("Por favor, carregue uma planilha do Excel.")
    return None

# Função para selecionar produtos
def selecionar_produtos(df):
    if df is not None and 'DESCRIÇÃO' in df.columns:
        produtos_disponiveis = df['DESCRIÇÃO'].tolist()
        produtos_selecionados = st.multiselect("Selecione os produtos", produtos_disponiveis)
        if not produtos_selecionados:
            st.warning("Nenhum produto selecionado.")
            return pd.DataFrame()
        df_selecionados = df[df['DESCRIÇÃO'].isin(produtos_selecionados)]
        return df_selecionados
    else:
        st.error("A coluna 'DESCRIÇÃO' não foi encontrada no DataFrame.")
    return pd.DataFrame()

# Função para adicionar preços e descontos aos produtos
def adicionar_preços_descontos(df):
    if df is not None:
        if 'DESCONTO' not in df.columns:
            df['DESCONTO'] = 0.0  # Adiciona a coluna DESCONTO caso não exista
        for index, row in df.iterrows():
            with st.expander(f"Produto: {row['DESCRIÇÃO']}"):
                preço = st.number_input(f"Preço de {row['DESCRIÇÃO']}", min_value=0.0, value=row['R$'], key=f"preço_{index}")
                desconto = st.number_input(f"Desconto (%) para {row['DESCRIÇÃO']}", min_value=0.0, max_value=100.0, value=row['DESCONTO'], key=f"desconto_{index}")
                df.at[index, 'R$'] = preço
                df.at[index, 'DESCONTO'] = desconto
        return df
    else:
        st.error("O DataFrame de produtos está vazio.")
    return pd.DataFrame()

# Função para calcular o orçamento
def calcular_orçamento(df_com_preços):
    if df_com_preços is not None and 'R$' in df_com_preços.columns and 'DESCONTO' in df_com_preços.columns:
        if 'Preço com desconto' not in df_com_preços.columns:
            df_com_preços['Preço com desconto'] = 0.0
        total = 0
        for index, row in df_com_preços.iterrows():
            preço_com_desconto = row['R$'] * (1 - row['DESCONTO'] / 100)
            df_com_preços.at[index, 'Preço com desconto'] = preço_com_desconto
            total += preço_com_desconto
        return df_com_preços, total
    else:
        st.error("Colunas 'R$' ou 'DESCONTO' ausentes.")
    return df_com_preços, 0

# Função para gerar o PDF do orçamento
def gerar_pdf(df_com_preços):
    if df_com_preços.empty:
        st.warning("O DataFrame está vazio. Não é possível gerar o PDF.")
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Orçamento de Produtos", ln=True, align='C')
    pdf.ln(10)

    # Cabeçalhos da tabela
    pdf.cell(40, 10, "Descrição", border=1)
    pdf.cell(40, 10, "Preço", border=1)
    pdf.cell(40, 10, "Desconto", border=1)
    pdf.cell(40, 10, "Preço com Desconto", border=1)
    pdf.ln()

    for index, row in df_com_preços.iterrows():
        pdf.cell(40, 10, row['DESCRIÇÃO'], border=1)
        pdf.cell(40, 10, f"R$ {row['R$']:.2f}", border=1)
        pdf.cell(40, 10, f"{row['DESCONTO']}%", border=1)
        pdf.cell(40, 10, f"R$ {row['Preço com desconto']:.2f}", border=1)
        pdf.ln()

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer
 
def main():
    st.title("Calculadora de Orçamento")

df = carregar_planilha()

if df is not None:
    df_selecionados = selecionar_produtos(df)
    if not df_selecionados.empty:
        df_com_preços = adicionar_preços_descontos(df_selecionados)
        df_com_preços, total = calcular_orçamento(df_com_preços)
        st.write("Orçamento Calculado:")
        st.dataframe(df_com_preços)

if st.button("Gerar orçamento em PDF"):
    buffer_pdf = gerar_pdf(df_com_preços)
    if buffer_pdf:
        st.download_button(
            label="Baixar Orçamento em PDF",
            data=buffer_pdf,
            file_name="orçamento.pdf",
            mime="application/pdf"
        )

if __name__=="__main__":
    main()
