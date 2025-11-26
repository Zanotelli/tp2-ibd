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

def cria_grafico_barras(df, titulo, coluna_categoria, coluna_valor, 
                       titulo_x='Total', titulo_y='Categoria', 
                       esquema_cores='blues', limite=None, altura=500):
    
    if limite and len(df) > limite:
        df = df.head(limite)
    
    st.subheader(titulo)
    
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{coluna_valor}:Q', 
                title=titulo_x,
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f'{coluna_categoria}:N', 
                title=titulo_y,
                sort='-x'),  # Ordenar por valor decrescente
        color=alt.Color(f'{coluna_valor}:Q',
                       scale=alt.Scale(scheme=esquema_cores),
                       legend=alt.Legend(title=titulo_x)),
        tooltip=[coluna_categoria, coluna_valor]
    ).properties(
        height=altura,
        title=titulo
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Opcional: exibir estatísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Itens", len(df))
    with col2:
        st.metric("Valor Máximo", df[coluna_valor].max())
    with col3:
        st.metric("Valor Mínimo", df[coluna_valor].min())
    return df


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

sql_req_municipio = """
SELECT req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE, COUNT(*) AS total_requisicoes
FROM Requisicao r
JOIN Requerentes req ON r.CNPJ_REQUERENTE = req.CNPJ_REQUERENTE
GROUP BY req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE
ORDER BY total_requisicoes DESC
LIMIT 10;
"""

sql_req_pais = """
SELECT o.PAIS, COUNT(*) AS total_pais
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
GROUP BY o.PAIS
ORDER BY total_pais DESC
LIMIT 10;
"""

sql_req_ano = """
SELECT o.ANO_PRODUCAO_INICIAL, COUNT(*) AS total_ano
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
GROUP BY o.ANO_PRODUCAO_INICIAL
ORDER BY total_ano DESC;
"""

st.title("Visualização de Dados do Banco SQLite")


col1, col2 = st.columns(2)

with col1:
    exibir_tabela(sql1)
with col2:
    exibir_tabela(sql3)


col1, col2 = st.columns(2)
with col1:
    df_municipios = fetch(sql_req_municipio, conn)
    df_municipios['MUNICIPIO_UF'] = df_municipios['MUNICIPIO_REQUERENTE'] + ' - ' + df_municipios['UF_REQUERENTE']

    # Usar a função genérica
    cria_grafico_barras(
        df_municipios,
        titulo="🏙️ Top 10 Municípios por Requisições",
        coluna_categoria='MUNICIPIO_UF',
        coluna_valor='total_requisicoes',
        titulo_x='Total de Requisições',
        titulo_y='Município - UF',
        esquema_cores='blues',
        altura=500
    )
with col2:
    df_pais = fetch(sql_req_pais, conn)

    # Usar a função genérica
    cria_grafico_barras(
        df_pais,
        titulo="🗺️ Top 10 Países por Requisições",
        coluna_categoria='PAIS',
        coluna_valor='total_pais',
        titulo_x='Total de Requisições',
        titulo_y='País de Origem',
        esquema_cores='blues',
        altura=500
    )


conn.close()