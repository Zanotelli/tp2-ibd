import streamlit as st
import pandas as pd
import sqlite3
import altair as alt


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
    # Executar a query e carregar no DataFrame
    df = fetch(query, conn)
    
    # Exibir a tabela no Streamlit
    st.dataframe(df)
    
    # Opcional: mostrar estatísticas básicas
    st.write(f"Total de registros: {len(df)}")



def cria_tabela_barras(sql):
    st.title("📊 Requisições por Município")
    
    df = fetch(sql, conn)
    
    df['MUNICIPIO_UF'] = df['MUNICIPIO_REQUERENTE'] + ' - ' + df['UF_REQUERENTE']
    
    st.subheader("Top 10 Municípios com Mais Requisições")
    
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('total_requisicoes:Q', 
                title='Total de Requisições',
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('MUNICIPIO_UF:N', 
                title='Município - UF',
                sort='-x'),  # Ordenar por valor decrescente
        color=alt.Color('total_requisicoes:Q',
                       scale=alt.Scale(scheme='blues'),
                       legend=alt.Legend(title="Total Requisições")),
        tooltip=['MUNICIPIO_REQUERENTE', 'UF_REQUERENTE', 'total_requisicoes']
    ).properties(
        width=800,
        height=500,
        title='Top 10 Municípios por Número de Requisições'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Estatísticas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Municípios", len(df))
    with col2:
        st.metric("Máximo de Requisições", df['total_requisicoes'].max())
    with col3:
        st.metric("Mínimo de Requisições", df['total_requisicoes'].min())

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

sql9 = """
SELECT req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE, COUNT(*) AS total_requisicoes
FROM Requisicao r
JOIN Requerentes req ON r.CNPJ_REQUERENTE = req.CNPJ_REQUERENTE
GROUP BY req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE
ORDER BY total_requisicoes DESC
LIMIT 10;
"""


# Interface do Streamlit
st.title("Visualização de Dados do Banco SQLite")
exibir_tabela(sql1)
exibir_tabela(sql3)
cria_tabela_barras(sql9)

conn.close()