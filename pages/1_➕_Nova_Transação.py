import streamlit as st
from datetime import date
from src.database import add_transaction

st.set_page_config(
    page_title="Nova Transação",
    page_icon="➕",
    layout="wide"
)

st.title("➕ Nova Transação")

with st.form("transaction_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        data_transacao = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        categoria = st.selectbox("Categoria", [
            "Alimentação", "Transporte", "Moradia", "Lazer", 
            "Saúde", "Educação", "Salário", "Investimentos", "Outros"
        ])
        
    with col2:
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        forma_pagto = st.selectbox("Pagamento", [
            "Crédito", "Débito", "Pix", "Dinheiro", "Boleto"
        ])
        descricao = st.text_input("Descrição (Opcional)")
        
    submitted = st.form_submit_button("Salvar Transação")
    
    if submitted:
        try:
            add_transaction(
                data_transacao, categoria, tipo, valor, forma_pagto, descricao
            )
            st.success("Transação salva com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
