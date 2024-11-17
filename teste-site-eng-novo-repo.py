import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import io

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

# Função para adicionar preços, descontos e quantidades aos produtos
def adicionar_preços_descontos_quantidade(df):
    if df is not None:
        if 'DESCONTO' not in df.columns:
            df['DESCONTO'] = 0.0  # Adiciona a coluna DESCONTO caso não exista
        if 'QUANTIDADE' not in df.columns:
            df['QUANTIDADE'] = 1  # Adiciona a coluna QUANTIDADE caso não exista

        for index, row in df.iterrows():
            with st.expander(f"Produto: {row['DESCRIÇÃO']}"):
                # Input para preço e desconto
                preço = st.number_input(f"Preço de {row['DESCRIÇÃO']}", min_value=0.0, value=row['R$'], key=f"preço_{index}")
                desconto = st.number_input(f"Desconto (%) para {row['DESCRIÇÃO']}", min_value=0.0, max_value=100.0, value=row['DESCONTO'], key=f"desconto_{index}")
                # Input para quantidade
                quantidade = st.number_input(f"Quantidade de {row['DESCRIÇÃO']}", min_value=1, value=1, key=f"quantidade_{index}")
                
                # Atualiza os valores no DataFrame
                df.at[index, 'R$'] = preço
                df.at[index, 'DESCONTO'] = desconto
                df.at[index, 'QUANTIDADE'] = quantidade
        return df
    else:
        st.error("O DataFrame de produtos está vazio.")
    return pd.DataFrame()

# Função para calcular o orçamento considerando as quantidades
def calcular_orçamento(df_com_preços):
    if df_com_preços is not None and 'R$' in df_com_preços.columns and 'DESCONTO' in df_com_preços.columns:
        if 'Preço com desconto' not in df_com_preços.columns:
            df_com_preços['Preço com desconto'] = 0.0
        if 'Total' not in df_com_preços.columns:
            df_com_preços['Total'] = 0.0
        total = 0
        for index, row in df_com_preços.iterrows():
            # Calcula o preço com desconto
            preço_com_desconto = row['R$'] * (1 - row['DESCONTO'] / 100)
            # Calcula o total com quantidade
            total_com_quantidade = preço_com_desconto * row['QUANTIDADE']
            
            df_com_preços.at[index, 'Preço com desconto'] = preço_com_desconto
            df_com_preços.at[index, 'Total'] = total_com_quantidade
            total += total_com_quantidade
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
    pdf.cell(40, 10, "Quantidade", border=1)
    pdf.cell(40, 10, "Preço com Desconto", border=1)
    pdf.cell(40, 10, "Total", border=1)
    pdf.ln()

    for index, row in df_com_preços.iterrows():
        pdf.cell(40, 10, row['DESCRIÇÃO'], border=1)
        pdf.cell(40, 10, f"R$ {row['R$']:.2f}", border=1)
        pdf.cell(40, 10, f"{row['DESCONTO']}%", border=1)
        pdf.cell(40, 10, f"{row['QUANTIDADE']}", border=1)
        pdf.cell(40, 10, f"R$ {row['Preço com desconto']:.2f}", border=1)
        pdf.cell(40, 10, f"R$ {row['Total']:.2f}", border=1)
        pdf.ln()

temp_dir = "/tmp/orcamentos"
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

caminho_arquivo_pdf = os.path.join(temp_dir, "orcamento.pdf")

pdf.output(caminho_arquivo_pdf)
    return caminho_arquivo_pdf

# Função principal do Streamlit
def main():
    st.title("Calculadora de Orçamento")

    # Carregar planilha
    df = carregar_planilha()

    if df is not None:
        # Selecionar produtos
        df_selecionados = selecionar_produtos(df)
        if not df_selecionados.empty:
            # Adicionar preços, descontos e quantidades
            df_com_preços = adicionar_preços_descontos_quantidade(df_selecionados)
            # Calcular orçamento
            df_com_preços, total = calcular_orçamento(df_com_preços)
            st.write("Orçamento Calculado:")
            st.dataframe(df_com_preços)

            # Gerar PDF quando botão for pressionado
            if st.button("Gerar orçamento em PDF"):
                caminho_pdf = gerar_pdf(df_com_preços)
                if caminho_pdf:
                    with open(caminho_pdf, "rb") as f:
                        st.download_button(
                            label="Baixar orçamento em PDF",
                            data=f,
                            file_name="orcamento.pdf",
                            mime="application/pdf"
                        )


if __name__ == "__main__":
    main()
