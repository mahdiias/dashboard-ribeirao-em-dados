#bibliotecas que devem ser baixadas
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

#pagina
st.set_page_config(layout="wide", page_title="Dashboard Ribeirão Preto", page_icon="📊")

#puxando os dados do dblocal
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

@st.cache_data

#funcao que realmente carrega os dados e verifica por meio de um if se foi encontrado
def carregar_dados_locais():
    if not os.path.exists(DB_PATH):
        st.error(f"Erro: O arquivo '{DB_FILE}' não foi encontrado!")
        st.warning("Execute o script 'db_local.py' primeiro para criar o banco de dados.")
        st.stop()
        
    conn = sqlite3.connect(DB_PATH)

    #tentativa de puxar tabelas especificas (e tratativa de erro)
    try:
        tabelas = {
            'territorio': pd.read_sql_query("SELECT * FROM territorio", conn),
            'demografia': pd.read_sql_query("SELECT * FROM demografia", conn),
            'saneamento': pd.read_sql_query("SELECT * FROM saneamento", conn),
            'pobreza': pd.read_sql_query("SELECT * FROM pobreza_desigualdade", conn),
            'mortalidade_causas': pd.read_sql_query("SELECT * FROM mortalidade_causas", conn)
        }
        return tabelas
    finally:
        conn.close()

#pega os dados e prepara eles para serem usados no resto do codigo
dados = carregar_dados_locais()
df_territorio = dados['territorio']
df_demografia = dados['demografia']
df_saneamento = dados['saneamento']
df_pobreza = dados['pobreza']
df_mortalidade_causas = dados['mortalidade_causas']

#titulo principal do dash
st.title("📊 Ribeirão em Dados")

#cria os filtros na barra lateral de 2022 a 2017 
st.sidebar.header("🔎 Filtros Interativos")
anos_disponiveis = sorted(df_mortalidade_causas['ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

#aqui é um subtitulo com um resumo geral de dados
st.subheader("Resumo Geral")

#aqui são os dados gerais do subheader
area = df_territorio.loc[df_territorio['indicador'] == 'Área da unidade territorial', 'valor'].iloc[0]
densidade = df_territorio.loc[df_territorio['indicador'] == 'Densidade demográfica', 'valor'].iloc[0]
incidencia_pobreza = df_pobreza.loc[df_pobreza['indicador'] == 'Incidência da pobreza', 'media'].iloc[0]
obitos_no_ano = df_mortalidade_causas[df_mortalidade_causas['ano'] == ano_selecionado]['obitos'].sum()

#exibicao dos dados do subheader
col1, col2, col3, col4 = st.columns(4)
col1.metric("Área Territorial", f"{area:,.2f} km²".replace(",", "."))
col2.metric("Densidade Demográfica", f"{densidade:,.2f} hab/km²".replace(",", "."))
col3.metric("Incidência de Pobreza", f"{incidencia_pobreza:.2f}%")
col4.metric(f"Óbitos Totais em {ano_selecionado}", f"{obitos_no_ano:,}".replace(",", "."))

st.divider()

#as 4 abas de navegaçao 
tab1, tab2, tab3, tab4 = st.tabs(["👤 População", "💧 Saneamento Básico", "⚖️ Pobreza e Desigualdade", "❤️ Saúde e Mortalidade"])

#aqui cria todo o layout da primeira aba
with tab1:
    
    st.header("População por sexo")

    #metricas da populacao por sexo
    pop_total = df_demografia['populacao'].sum()
    pop_masc = df_demografia[df_demografia['sexo'] == 'Masculino']['populacao'].sum()
    pop_fem = df_demografia[df_demografia['sexo'] == 'Feminino']['populacao'].sum()

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("População Geral", f"{pop_total:,}".replace(",", "."))
    col_b.metric("População Masculina", f"{pop_masc:,}".replace(",", "."))
    col_c.metric("População Feminina", f"{pop_fem:,}".replace(",", "."))
    
    #o filtro para populacao a partir do sexo
    st.subheader("População por cor ou raça")
    sexo_grafico = st.radio(
        "Filtrar gráfico por Sexo:",
        ['Ambos', 'Masculino', 'Feminino'],
        horizontal=True,
        key="sexo_grafico_pop" # Chave única para este widget
    )
    #aqui cria os gráficos
    df_demografia_filtrado = df_demografia.copy()
    if sexo_grafico != 'Ambos':
        df_demografia_filtrado = df_demografia[df_demografia['sexo'] == sexo_grafico]
    
    fig_pop_raca = px.bar(
        df_demografia_filtrado, 
        x='raca', 
        y='populacao', 
        color='sexo', 
        text_auto=True, 
        barmode='group'
    )
    st.plotly_chart(fig_pop_raca, use_container_width=True)

#aqui cria todo o layout da segunda aba
with tab2:
    #header da aba
    st.header("Condições de Saneamento nos Domicílios")
    col1, col2, col3 = st.columns(3)
    #abaixo cria os gráficos de pizza com os dados especificos
    with col1:
        df_servico = df_saneamento[df_saneamento['servico'] == 'Esgotamento']
        fig = px.pie(df_servico, names='tipo', values='domicilios', title='Tipo de Esgotamento Sanitário', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        df_servico = df_saneamento[df_saneamento['servico'] == 'Lixo']
        fig = px.pie(df_servico, names='tipo', values='domicilios', title='Destino do Lixo Doméstico', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with col3:
        df_servico = df_saneamento[df_saneamento['servico'] == 'Banheiros']
        fig = px.pie(df_servico, names='tipo', values='domicilios', title='Nº de Banheiros por Domicílio', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

#aqui cria todo o layout da terceira aba
with tab3:
    #header da aba
    st.header("Indicadores de Pobreza e Desigualdade")
    st.markdown("Os gráficos mostram a média e o intervalo de confiança (limite inferior e superior) para cada indicador.")
    
    #abaixo puxa os dados e criam os graficos de barras
    df_pobreza_fmt = df_pobreza.copy()
    df_pobreza_fmt['indicador'] = df_pobreza_fmt['indicador'].str.replace('Incidência da pobreza subjetiva', 'Pobreza Subjetiva')
    df_pobreza_fmt['indicador'] = df_pobreza_fmt['indicador'].str.replace('Incidência da pobreza', 'Pobreza')

    fig_pobreza = px.bar(
        df_pobreza_fmt,
        x='indicador',
        y='media',
        error_y=df_pobreza_fmt['limite_superior'] - df_pobreza_fmt['media'],
        error_y_minus=df_pobreza_fmt['media'] - df_pobreza_fmt['limite_inferior'],
        title='Indicadores com Intervalo de Confiança',
        labels={'indicador': 'Indicador', 'media': 'Valor (em % para Pobreza)'},
        text_auto='.2f'
    )
    #aqui vc consegue ver a tabela dos dados gerais
    st.plotly_chart(fig_pobreza, use_container_width=True)
    with st.expander("Ver tabela de dados detalhados"):
        st.dataframe(df_pobreza)

with tab4:
    #header da aba
    st.header(f"Análise de Mortalidade ({ano_selecionado})")
    
    #puxa os dados e cria os graficos de barra tbm
    df_causas_filtrado = df_mortalidade_causas[df_mortalidade_causas['ano'] == ano_selecionado]
    df_causas_top = df_causas_filtrado.nlargest(10, 'obitos')
    
    fig_morte = px.bar(
        df_causas_top.sort_values('obitos'),
        x='obitos',
        y='causa',
        orientation='h',
        text='obitos',
        title=f"Principais Causas de Morte em {ano_selecionado}"
    )
    st.plotly_chart(fig_morte, use_container_width=True)

    #aqui vc consegue ver a tabela dos dados gerais
    with st.expander("Ver tabela completa de causas de mortalidade"):
        st.dataframe(df_causas_filtrado.sort_values('obitos', ascending=False), use_container_width=True)