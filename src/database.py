import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import uuid
import streamlit as st

# Nome da Planilha
SPREADSHEET_NAME = "financeiro_db"

def get_worksheet():
    """Conecta ao Google Sheets e retorna a primeira aba."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Tenta conectar. Usa st.cache_resource para não reconectar a cada reload
    try:
        # Tenta pegar dos secrets do Streamlit (formato de dicionário)
        # O Streamlit carrega automaticamente .streamlit/secrets.toml (Local) ou Secrets (Cloud)
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            
        client = gspread.authorize(creds)
        
        # Abre a planilha
        sheet = client.open(SPREADSHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        st.stop()

def init_db():
    """Inicializa a planilha com os cabeçalhos se estiver vazia."""
    try:
        sheet = get_worksheet()
        # Verifica se a primeira célula está vazia (indica planilha nova)
        if sheet.acell('A1').value is None:
            # Cabeçalhos
            headers = ["id", "date", "category", "type", "amount", "payment_method", "description"]
            sheet.append_row(headers)
            print("Cabeçalhos criados no Google Sheets!")
    except Exception as e:
        print(f"Erro ao conectar com Google Sheets: {e}")

def clean_amount(value):
    """Trata valores numéricos vindos da planilha (floats ou strings formatadas)."""
    # Debug para o console do Streamlit Cloud
    print(f"DEBUG_CLEAN: Entrada={repr(value)} Tipo={type(value)}")

    if isinstance(value, (int, float)):
        return float(value)
        
    if isinstance(value, str):
        # Remove espaços e R$
        value = value.replace("R$", "").strip()
        
        if not value:
            return 0.0
            
        # O Google Sheets as vezes manda formatos com ponto de milhar se estiver configurado errado
        # Se UNFORMATTED_VALUE funcionar, nem deveríamos cair aqui com tanta frequencia para números.
        
        # Analise de ambiguidade:
        # Se tem APENAS UM PONTO e NENHUMA VIRGULA (ex: "570.15"), é decimal (formato US/Python).
        if "." in value and "," not in value:
            if value.count(".") == 1:
                try:
                    return float(value)
                except ValueError:
                    pass

        # Se tem virgula (ex: "570,15" ou "1.000,50"), assume formato BR
        # Também cobre casos estranhos onde ponto é milhar ("1.000")
        try:
            # Remove ponto de milhar e troca virgula decimal por ponto
            v_br = value.replace(".", "").replace(",", ".")
            return float(v_br)
        except ValueError:
            return 0.0
            
    return 0.0

def add_transaction(date, category, transaction_type, amount, payment_method, description):
    """Adiciona uma nova transação na planilha."""
    sheet = get_worksheet()
    
    # Gera um ID único (UUID) pois planilhas não tem auto-incremento confiável
    new_id = str(uuid.uuid4())
    
    # Prepara a linha (Converta valores para string/float conforme necessário)
    # Importante: enviar float nativo para o Sheets salvar como número
    row = [
        new_id,
        str(date),
        category,
        transaction_type,
        float(amount),
        payment_method,
        description
    ]
    
    sheet.append_row(row)

def get_transactions():
    """Retorna todas as transações como um DataFrame do Pandas."""
    try:
        sheet = get_worksheet()
        # UNFORMATTED_VALUE garante que números venham como floats e não strings formatadas (R$ ...)
        data = sheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
        
        # Se estiver vazio (nem cabeçalho tem), tenta inicializar
        if not data:
            init_db()
            # Tenta pegar de novo
            data = sheet.get_all_records()
            if not data:
                 return pd.DataFrame(columns=["id", "date", "category", "type", "amount", "payment_method", "description"])
            
        df = pd.DataFrame(data)
        
        # Garante que 'amount' é numérico (planilha as vezes retorna como string)
        # Remove símbolos de moeda se houver (ex: "R$ 100") e substitui vírgula
        if not df.empty and "amount" in df.columns:
             # Aplica a limpeza robusta em cada valor
             df["amount"] = df["amount"].apply(clean_amount)
             
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

def get_transaction(transaction_id):
    """Busca uma transação específica pelo ID."""
    df = get_transactions()
    transaction = df[df["id"] == str(transaction_id)]
    return transaction.iloc[0] if not transaction.empty else None

def delete_transaction(transaction_id):
    """Remove uma transação baseada no ID."""
    sheet = get_worksheet()
    
    # Busca a célula que contém o ID
    cell = sheet.find(str(transaction_id))
    
    if cell:
        sheet.delete_rows(cell.row)

def update_transaction(transaction_id, date, category, transaction_type, amount, payment_method, description):
    """Atualiza uma transação existente."""
    sheet = get_worksheet()
    
    # Busca a célula do ID para saber qual linha editar
    cell = sheet.find(str(transaction_id))
    
    if cell:
        row_idx = cell.row
        # Atualiza as colunas (B=2=Data, C=3=Categoria, etc...)
        # A API tem update_cell(row, col, value)
        
        # Otimização: update uma linha inteira seria melhor, mas update_cell é mais simples de entender
        sheet.update_cell(row_idx, 2, str(date))            # date
        sheet.update_cell(row_idx, 3, category)             # category
        sheet.update_cell(row_idx, 4, transaction_type)     # type
        sheet.update_cell(row_idx, 5, float(amount))        # amount
        sheet.update_cell(row_idx, 6, payment_method)       # payment_method
        sheet.update_cell(row_idx, 7, description)          # description

# Inicializa ao importar/rodar
if __name__ == "__main__":
    init_db()