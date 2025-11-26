import streamlit as st
import pandas as pd
import sqlite3


def fetch(query, conn, formatted=True):
    # execute the query and fetch all rows
    cur = conn.cursor()
    cur.execute(query)
    rs = cur.fetchall()

    # extract column names from the cursor description
    columns = [desc[0] for desc in cur.description]

    # return a dataframe with column names
    return pd.DataFrame(rs, columns=columns) if formatted else rs

def exibir_tabela(query):
    
    try:
        # Executar a query e carregar no DataFrame
        df = fetch(query, conn)
        
        # Exibir a tabela no Streamlit
        st.dataframe(df)
        
        # Opcional: mostrar estatísticas básicas
        st.write(f"Total de registros: {len(df)}")
        
    except Exception as e:
        st.error(f"Erro ao executar a query: {e}")
    finally:
        conn.close()

#-------------------------------------------------------------
st.set_page_config(
    page_title="Dados Ancine",
    page_icon="🎥"
)

conn = sqlite3.connect('ancine.db')

sql1 = """
SELECT CRT, CNPJ_REQUERENTE, SITUACAO_CRT, DATA_REQUERIMENTO_CRT
FROM Requisicao
WHERE SITUACAO_CRT = 'IRREGULAR'
LIMIT 50;
"""



# Interface do Streamlit
st.title("Visualização de Dados do Banco SQLite")
exibir_tabela(sql1)