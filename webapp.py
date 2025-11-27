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
    df = fetch(query, conn)

    column_config = {}
    for col in df.columns:
        column_config[col] = st.column_config.Column(
            col,
            help=f"Pesquisar em {col}",
        )
    
    st.dataframe(
        df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True
    )
    
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
    
    return df

def cria_grafico_linhas_ano(sql_req_ano, conn, titulo="Evolução de Requisições por Ano"):

    df = fetch(sql_req_ano, conn)
    
    # Ordenar por ano para garantir a sequência temporal correta
    df = df.sort_values('ANO_PRODUCAO_INICIAL')
    
    st.subheader(titulo)
    
    # Criar gráfico de linhas
    line_chart = alt.Chart(df).mark_line(
        point=True,  # Adiciona pontos em cada dado
        strokeWidth=3,
        color='#1f77b4'
    ).encode(
        x=alt.X('ANO_PRODUCAO_INICIAL:N', 
                title='Ano de Produção Inicial',
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('total_ano:Q', 
                title='Total de Requisições',
                axis=alt.Axis(grid=True)),
        tooltip=['ANO_PRODUCAO_INICIAL', 'total_ano']
    ).properties(
        height=400,
        title=titulo
    )
    
    # Adicionar área sob a linha (opcional)
    area_chart = alt.Chart(df).mark_area(
        opacity=0.3,
        color='#1f77b4'
    ).encode(
        x='ANO_PRODUCAO_INICIAL:N',
        y='total_ano:Q'
    )
    
    # Combinar linha e área
    chart = (area_chart + line_chart).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Anos", len(df))
    with col2:
        st.metric("Ano com Mais Requisições", 
                 f"{df.loc[df['total_ano'].idxmax(), 'ANO_PRODUCAO_INICIAL']}",
                 f"{df['total_ano'].max()}")
    with col3:
        st.metric("Ano com Menos Requisições", 
                 f"{df.loc[df['total_ano'].idxmin(), 'ANO_PRODUCAO_INICIAL']}",
                 f"{df['total_ano'].min()}")
    with col4:
        crescimento = ((df['total_ano'].iloc[-1] - df['total_ano'].iloc[0]) / df['total_ano'].iloc[0] * 100) if len(df) > 1 else 0
        st.metric("Crescimento Total", f"{crescimento:.1f}%")
    
    return df

#-------------------------------------------------------------
st.set_page_config(
    page_title="Dados Ancine",
    page_icon="🎥",
    layout="wide"
)

conn = sqlite3.connect('ancine.db')

# ========== NOVO: FILTRO DE ANO ==========
st.sidebar.header("🔍 Filtros")

# Input para digitar o ano
ano_filtro = st.sidebar.text_input(
    "Filtrar por ano de requisição:",
    placeholder="Ex: 2023, 2022, 2021",
    help="Digite um ou mais anos separados por vírgula"
)

# Construir a query base
sql3_base = """
SELECT r.CRT, o.TITULO_ORIGINAL as "Título", o.PAIS as "País de origem", r.SITUACAO_CRT as "Situação",
r.DATA_REQUERIMENTO_CRT as "Data da requisição"
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
"""

sql_req_ano = """
SELECT o.ANO_PRODUCAO_INICIAL, COUNT(*) AS total_ano
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
"""

# Aplicar filtro se ano foi digitado
if ano_filtro.strip():
    # Limpar e separar os anos
    anos = [ano.strip() for ano in ano_filtro.split(',') if ano.strip()]
    
    if anos:
        condicoes = []
        for ano in anos:
            condicoes.append(f"r.DATA_REQUERIMENTO_CRT LIKE '%{ano}%'")
        
        where_clause = " WHERE " + " OR ".join(condicoes)
        sql3 = sql3_base + where_clause + ";"
        sql_req_ano = sql_req_ano + where_clause
        
        st.sidebar.success(f"Filtrando por ano(s): {', '.join(anos)}")
    else:
        sql3 = sql3_base + ";"
else:
    sql3 = sql3_base + ";"

sql_req_ano = sql_req_ano + " GROUP BY o.ANO_PRODUCAO_INICIAL ORDER BY total_ano DESC;"
# ========== FIM DO NOVO FILTRO ==========

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


st.title("Visualização de Dados de Requisições de obras não publicitárias - Ancine 🎥")

# Mostrar informação do filtro ativo
if ano_filtro.strip():
    anos = [ano.strip() for ano in ano_filtro.split(',') if ano.strip()]
    if anos:
        st.info(f"📅 **Filtro ativo:** Mostrando requisições dos anos {', '.join(anos)}")

exibir_tabela(sql3)

df_anos = cria_grafico_linhas_ano(sql_req_ano, conn)


st.markdown("---")
st.header("📊 Estatísticas gerais")

df_municipios = fetch(sql_req_municipio, conn)
df_municipios['MUNICIPIO_UF'] = df_municipios['MUNICIPIO_REQUERENTE'] + ' - ' + df_municipios['UF_REQUERENTE']
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
df_pais = fetch(sql_req_pais, conn)
cria_grafico_barras(
    df_pais,
    titulo="🗺️ Top 10 Países por Requisições",
    coluna_categoria='PAIS',
    coluna_valor='total_pais',
    titulo_x='Total de Requisições',
    titulo_y='País de Origem',
    esquema_cores='reds',
    altura=500
)

#---

conn.close()