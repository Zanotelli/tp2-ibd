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

def aplicar_filtro_ano(query_base, ano_filtro):
    """
    Aplica filtro de ano às queries, verificando DATA_REQUERIMENTO_CRT e TITULO_ORIGINAL
    """
    if not ano_filtro:
        return query_base
    
    # Remove LIMIT se existir para aplicar WHERE corretamente
    query_sem_limit = query_base.split('LIMIT')[0] if 'LIMIT' in query_base else query_base
    
    # Adiciona WHERE ou AND dependendo da query
    if 'WHERE' in query_sem_limit.upper():
        where_clause = f"AND (strftime('%Y', r.DATA_REQUERIMENTO_CRT) = '{ano_filtro}' OR o.TITULO_ORIGINAL LIKE '%{ano_filtro}%')"
    else:
        where_clause = f"WHERE (strftime('%Y', r.DATA_REQUERIMENTO_CRT) = '{ano_filtro}' OR o.TITULO_ORIGINAL LIKE '%{ano_filtro}%')"
    
    # Re-adiciona LIMIT se existia originalmente
    if 'LIMIT' in query_base:
        limit_clause = 'LIMIT' + query_base.split('LIMIT')[1]
        return query_sem_limit + ' ' + where_clause + ' ' + limit_clause
    else:
        return query_sem_limit + ' ' + where_clause

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

# QUERIES BASE (sem filtro)
sql3_base = """
SELECT r.CRT, o.TITULO_ORIGINAL as "Título", r.SITUACAO_CRT as "Situação",
r.DATA_REQUERIMENTO_CRT as "Data da requisição"
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
"""

sql_req_municipio_base = """
SELECT req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE, COUNT(*) AS total_requisicoes
FROM Requisicao r
JOIN Requerentes req ON r.CNPJ_REQUERENTE = req.CNPJ_REQUERENTE
GROUP BY req.MUNICIPIO_REQUERENTE, req.UF_REQUERENTE
ORDER BY total_requisicoes DESC
"""

sql_req_pais_base = """
SELECT o.PAIS, COUNT(*) AS total_pais
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
GROUP BY o.PAIS
ORDER BY total_pais DESC
"""

sql_req_ano_base = """
SELECT o.ANO_PRODUCAO_INICIAL, COUNT(*) AS total_ano
FROM Requisicao r
JOIN Obras o ON r.CRT = o.CRT
GROUP BY o.ANO_PRODUCAO_INICIAL
ORDER BY total_ano DESC
"""

st.title("Visualização de Dados do Banco SQLite")

# FILTRO DE ANO - Adicionado aqui
st.sidebar.header("🔍 Filtros")
ano_filtro = st.sidebar.text_input(
    "Filtrar por Ano:",
    placeholder="Ex: 2023, 2022...",
    help="Filtra por DATA_REQUERIMENTO_CRT ou TITULO_ORIGINAL contendo o ano"
)

# Aplicar filtro às queries
sql3_filtrado = aplicar_filtro_ano(sql3_base, ano_filtro) + " LIMIT 50"
sql_req_municipio_filtrado = aplicar_filtro_ano(sql_req_municipio_base, ano_filtro) + " LIMIT 10"
sql_req_pais_filtrado = aplicar_filtro_ano(sql_req_pais_base, ano_filtro) + " LIMIT 10"
sql_req_ano_filtrado = aplicar_filtro_ano(sql_req_ano_base, ano_filtro)

# Indicador de filtro ativo
if ano_filtro:
    st.sidebar.success(f"✅ Filtro ativo: Ano {ano_filtro}")
    st.sidebar.info(f"Filtrando por:\n- DATA_REQUERIMENTO_CRT = {ano_filtro}\n- TITULO_ORIGINAL contém '{ano_filtro}'")

# EXIBIÇÃO DOS DADOS FILTRADOS
exibir_tabela(sql3_filtrado)

col1, col2 = st.columns(2)
with col1:
    df_municipios = fetch(sql_req_municipio_filtrado, conn)
    if not df_municipios.empty:
        df_municipios['MUNICIPIO_UF'] = df_municipios['MUNICIPIO_REQUERENTE'] + ' - ' + df_municipios['UF_REQUERENTE']
        cria_grafico_barras(
            df_municipios,
            titulo="🏙️ Top 10 Municípios por Requisições" + (f" ({ano_filtro})" if ano_filtro else ""),
            coluna_categoria='MUNICIPIO_UF',
            coluna_valor='total_requisicoes',
            titulo_x='Total de Requisições',
            titulo_y='Município - UF',
            esquema_cores='blues',
            altura=500
        )
    else:
        st.warning("Nenhum dado encontrado para o filtro aplicado.")

with col2:
    df_pais = fetch(sql_req_pais_filtrado, conn)
    if not df_pais.empty:
        cria_grafico_barras(
            df_pais,
            titulo="🗺️ Top 10 Países por Requisições" + (f" ({ano_filtro})" if ano_filtro else ""),
            coluna_categoria='PAIS',
            coluna_valor='total_pais',
            titulo_x='Total de Requisições',
            titulo_y='País de Origem',
            esquema_cores='reds',
            altura=500
        )
    else:
        st.warning("Nenhum dado encontrado para o filtro aplicado.")

# Gráfico de linhas
df_anos = cria_grafico_linhas_ano(sql_req_ano_filtrado, conn)

conn.close()