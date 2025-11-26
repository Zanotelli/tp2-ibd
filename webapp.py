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
SELECT TITULO_ORIGINAL, PAIS
FROM Obras
WHERE ANO_PRODUCAO_INICIAL = 2005
LIMIT 50;
"""

sql3 = """
SELECT r.CRT, o.TITULO_BRASIL, r.SITUACAO_CRT
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
LIMIT 50;
"""

sql4 = """
SELECT r.id, r.nome_requerente, COUNT(req.CRT) AS total_requisicoes
FROM Requerente r
JOIN Requisicao req ON r.cnpj = req.CNPJ_REQUERENTE
GROUP BY r.id, r.nome_requerente
ORDER BY total_requisicoes DESC
LIMIT 50;
"""


# Interface do Streamlit
st.title("Visualização de Dados do Banco SQLite")
exibir_tabela(sql1)
exibir_tabela(sql3)
exibir_tabela(sql4)