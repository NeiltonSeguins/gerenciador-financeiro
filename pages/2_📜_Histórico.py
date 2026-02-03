import streamlit as st
from src.database import get_transactions, delete_transaction
import pandas as pd
from datetime import date
import time

st.set_page_config(
    page_title="Histórico",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Histórico de Transações")

df = get_transactions()

if df.empty:
    st.info("Nenhuma transação encontrada.")
else:
    # --- FILTROS AVANÇADOS ---
    st.sidebar.header("Filtros")
    
    # Prepara dados para filtros
    df["date"] = pd.to_datetime(df["date"])
    
    # 1. Filtro de Data (Ano/Mês)
    anos = sorted(df["date"].dt.year.unique(), reverse=True)
    # Adiciona opção "Todos"
    ano_filtro = st.sidebar.selectbox("Ano", ["Todos"] + list(anos))
    
    meses_dict = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    mes_filtro = st.sidebar.selectbox("Mês", ["Todos"] + list(meses_dict.values()))
    
    # 2. Filtro de Categoria
    categorias_unicas = sorted(df["category"].unique())
    categorias_filtro = st.sidebar.multiselect("Categoria", categorias_unicas, default=categorias_unicas)

    # 3. Filtro de Pagamento
    pagamentos_unicos = sorted(df["payment_method"].dropna().unique())
    pagamentos_filtro = st.sidebar.multiselect("Forma de Pagamento", pagamentos_unicos, default=pagamentos_unicos)

    # --- APLICAÇÃO DOS FILTROS ---
    df_filtered = df.copy()
    
    if ano_filtro != "Todos":
        df_filtered = df_filtered[df_filtered["date"].dt.year == ano_filtro]
        
    if mes_filtro != "Todos":
        # Inverte o dict para achar o número do mês
        mes_num = list(meses_dict.keys())[list(meses_dict.values()).index(mes_filtro)]
        df_filtered = df_filtered[df_filtered["date"].dt.month == mes_num]
        
    if categorias_filtro:
        df_filtered = df_filtered[df_filtered["category"].isin(categorias_filtro)]
        
    if pagamentos_filtro:
        df_filtered = df_filtered[df_filtered["payment_method"].isin(pagamentos_filtro)]

    # --- EXIBIÇÃO ---
    if df_filtered.empty:
        st.warning("Nenhuma transação encontrada com esses filtros.")
    else:
        # Ordenação
        df_filtered = df_filtered.sort_values(by="date", ascending=False)
        df_filtered = df_filtered.reset_index(drop=True)
        
        # Tabela
        event = st.dataframe(
            df_filtered,
            column_config={
                "date": "Data",
                "category": "Categoria",
                "type": "Tipo",
                "amount": st.column_config.NumberColumn(
                    "Valor (R$)",
                    format="R$ %.2f"
                ),
                "payment_method": "Pagamento",
                "description": "Descrição",
                "id": None
            },
            width="stretch", 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Painel de Ações
        if len(event.selection.rows) > 0:
            row_index = event.selection.rows[0]
            # IMPORTANTE: Pegar o ID do dataframe filtrado, não do original
            selected_id = df_filtered.iloc[row_index]["id"]
            
            st.divider()
            st.subheader("Gerenciar Transação Selecionada")
            
            col1, col2 = st.columns(2)
            
            if col1.button("✏️ Editar Transação", type="primary"):
                st.session_state["transaction_id_to_edit"] = selected_id
                st.switch_page("pages/3_✏️_Editar_Transação.py")
                
            if col2.button("🗑️ Excluir Transação", type="secondary"):
                try:
                    delete_transaction(selected_id)
                    st.success("Transação excluída com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
