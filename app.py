import streamlit as st
import plotly.express as px
from datetime import date
import pandas as pd
from src.database import get_transactions

# Configuração da Página deve sempre ser a primeira coisa
st.set_page_config(
    page_title="Dashboard - Finanças",
    page_icon="💰",
    layout="wide"
)

def main():
    st.title("📊 Dashboard Financeiro")
    
    # Busca dados
    df = get_transactions()
    
    if df.empty:
        st.info("Nenhuma transação encontrada. Vá até a página de 'Nova Transação' no menu lateral para começar.")
        return

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    
    # Converte coluna de data para datetime se ainda não for
    df["date"] = pd.to_datetime(df["date"])
    
    # Extrai anos disponíveis e meses
    anos = sorted(df["date"].dt.year.unique(), reverse=True)
    mes_atual = date.today().month
    ano_atual = date.today().year
    
    # Se não tiver dados suficientes, usa o atual
    if not anos:
        anos = [ano_atual]
        
    ano_selecionado = st.sidebar.selectbox("Ano", anos, index=0)
    
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    mes_selecionado = st.sidebar.selectbox("Mês", list(meses.keys()), format_func=lambda x: meses[x], index=mes_atual-1)
    
    # Aplica o filtro
    df_filtered = df[
        (df["date"].dt.year == ano_selecionado) & 
        (df["date"].dt.month == mes_selecionado)
    ]
    
    # Exibe contexto
    st.markdown(f"**Periodo:** {meses[mes_selecionado]} / {ano_selecionado}")
    
    if df_filtered.empty:
        st.warning("Nenhum dado para este período.")
        return

    # 1. KPIs
    # Receitas e Despesas (Apenas do mês selecionado - Fluxo de Caixa)
    receitas_mes = df_filtered[df_filtered["type"] == "Receita"]["amount"].sum()
    despesas_mes = df_filtered[df_filtered["type"] == "Despesa"]["amount"].sum()
    
    # Saldo (Acumulado até o final do mês selecionado - Patrimônio)
    # Pega tudo que é anterior ou do mesmo mês/ano selecionado
    df_accumulated = df[
        (df["date"].dt.year < ano_selecionado) | 
        ((df["date"].dt.year == ano_selecionado) & (df["date"].dt.month <= mes_selecionado))
    ]
    
    receitas_total = df_accumulated[df_accumulated["type"] == "Receita"]["amount"].sum()
    despesas_total = df_accumulated[df_accumulated["type"] == "Despesa"]["amount"].sum()
    saldo_acumulado = receitas_total - despesas_total
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo Acumulado", f"R$ {saldo_acumulado:,.2f}", help="Total acumulado desde o início até o final deste mês")
    col2.metric("Receitas (Mês)", f"R$ {receitas_mes:,.2f}", delta="Entradas")
    col3.metric("Despesas (Mês)", f"R$ {despesas_mes:,.2f}", delta="-Saídas", delta_color="inverse")
    
    st.divider()
    
    # 2. Gráficos
    c1, c2 = st.columns(2)
    
    # Gráfico de Pizza (Despesas)
    df_despesas = df_filtered[df_filtered["type"] == "Despesa"]
    if not df_despesas.empty:
        fig_cat = px.pie(
            df_despesas, 
            names="category", 
            values="amount", 
            title="Distribuição de Despesas",
            hole=0.4
        )
        c1.plotly_chart(fig_cat, width="stretch")
    else:
        c1.info("Sem dados de despesas para gráfico.")
        
    # Gráfico de Barras (Evolução)
    df_timeline = df_filtered.groupby(["date", "type"])["amount"].sum().reset_index()
    fig_time = px.bar(
        df_timeline, 
        x="date", 
        y="amount", 
        color="type",
        title="Evolução Financeira",
        barmode="group",
        color_discrete_map={"Receita": "green", "Despesa": "red"}
    )
    c2.plotly_chart(fig_time, width="stretch")

if __name__ == "__main__":
    main()