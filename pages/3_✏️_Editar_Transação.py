import streamlit as st
import pandas as pd
from datetime import date
from src.database import get_transaction, update_transaction

st.set_page_config(
    page_title="Editar Transação",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ Editar Transação")

# Verifica se há um ID selecionado na sessão
if "transaction_id_to_edit" not in st.session_state:
    st.warning("Nenhuma transação selecionada para edição.")
    st.info("Vá para a página de 'Histórico', selecione uma linha e clique em 'Editar'.")
    if st.button("Ir para Histórico"):
        st.switch_page("pages/2_📜_Histórico.py")
    st.stop()

transaction_id = st.session_state["transaction_id_to_edit"]
transacao = get_transaction(transaction_id)

if transacao is None:
    st.error("Transação não encontrada ou já excluída.")
    if st.button("Voltar"):
        st.switch_page("pages/2_📜_Histórico.py")
    st.stop()

# Preenche o formulário com os dados existentes
with st.form("edit_transaction_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Prevenção de erro na conversão de string para data
        data_atual = pd.to_datetime(transacao["date"]).date()
        
        data_transacao = st.date_input("Data", value=data_atual)
        
        # Índices para selectbox
        tipos = ["Despesa", "Receita"]
        idx_tipo = tipos.index(transacao["type"]) if transacao["type"] in tipos else 0
        tipo = st.selectbox("Tipo", tipos, index=idx_tipo)
        
        categorias = [
            "Alimentação", "Transporte", "Moradia", "Lazer", 
            "Saúde", "Educação", "Salário", "Investimentos", "Outros"
        ]
        cat_index = categorias.index(transacao["category"]) if transacao["category"] in categorias else 8
        categoria = st.selectbox("Categoria", categorias, index=cat_index)
        
    with col2:
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", value=float(transacao["amount"]))
        
        pagamentos = ["Crédito", "Débito", "Pix", "Dinheiro", "Boleto"]
        pagto_index = pagamentos.index(transacao["payment_method"]) if transacao["payment_method"] in pagamentos else 0
        forma_pagto = st.selectbox("Pagamento", pagamentos, index=pagto_index)
        
        descricao = st.text_input("Descrição (Opcional)", value=transacao["description"] if transacao["description"] else "")
        
    col_save, col_cancel = st.columns([1, 4])
    with col_save:
        submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
    
    if submitted:
        try:
            update_transaction(
                transaction_id, data_transacao, categoria, tipo, valor, forma_pagto, descricao
            )
            st.success("Transação atualizada com sucesso!")
            # Limpa sessão e volta pro histórico
            del st.session_state["transaction_id_to_edit"]
            st.switch_page("pages/2_📜_Histórico.py")
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

if st.button("Cancelar"):
    del st.session_state["transaction_id_to_edit"]
    st.switch_page("pages/2_📜_Histórico.py")
