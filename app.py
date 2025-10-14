import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import json

# Configuração da página
st.set_page_config(layout="wide", page_title="Ribeirão em Dados", page_icon="🗺️")

# --- Conexão e Carregamento de Dados ---
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)
MAP_FILE_PATH = os.path.join(DATA_DIR, "mapa-bairros-ribeirao-preto.geojson")

@st.cache_data
def carregar_dados_locais():
    if not os.path.exists(DB_PATH):
        st.error(f"Erro: O arquivo '{DB_FILE}' não foi encontrado! Execute 'db_local.py' primeiro.")
        st.stop()
    conn = sqlite3.connect(DB_PATH)
    try:
        tabelas = {
            'territorio': pd.read_sql_query("SELECT * FROM territorio", conn),
            'demografia': pd.read_sql_query("SELECT * FROM demografia", conn),
            'saneamento': pd.read_sql_query("SELECT * FROM saneamento", conn),
            'pobreza': pd.read_sql_query("SELECT * FROM pobreza_desigualdade", conn),
            'mortalidade_causas': pd.read_sql_query("SELECT * FROM mortalidade_causas", conn),
            'dados_bairros': pd.read_sql_query("SELECT * FROM dados_bairros", conn)
        }
        return tabelas
    finally:
        conn.close()

@st.cache_data
def carregar_mapa():
    if not os.path.exists(MAP_FILE_PATH):
        st.error(f"Erro: Arquivo '{os.path.basename(MAP_FILE_PATH)}' não encontrado na pasta 'data/'!")
        st.info("Por favor, crie o arquivo GeoJSON manualmente conforme as instruções.")
        return None
    with open(MAP_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Preparação dos Dados ---
dados = carregar_dados_locais()
geojson = carregar_mapa()
df_territorio = dados['territorio']
df_demografia = dados['demografia']
df_saneamento = dados['saneamento']
df_pobreza = dados['pobreza']
df_mortalidade_causas = dados['mortalidade_causas']
df_bairros = dados['dados_bairros']

# --- Interface Principal ---
st.title("🗺️ Ribeirão em Dados")

st.sidebar.header("🔎 Filtros Interativos")
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", sorted(df_mortalidade_causas['ano'].unique(), reverse=True))

st.subheader("Resumo Geral")
area = df_territorio.loc[df_territorio['indicador'] == 'Área da unidade territorial', 'valor'].iloc[0]
densidade = df_territorio.loc[df_territorio['indicador'] == 'Densidade demográfica', 'valor'].iloc[0]
incidencia_pobreza = df_pobreza.loc[df_pobreza['indicador'] == 'Incidência da pobreza', 'media'].iloc[0]
obitos_no_ano = df_mortalidade_causas[df_mortalidade_causas['ano'] == ano_selecionado]['obitos'].sum()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Área Territorial", f"{area:,.2f} km²")
col2.metric("Densidade Demográfica", f"{densidade:,.2f} hab/km²")
col3.metric("Incidência de Pobreza", f"{incidencia_pobreza:.2f}%")
col4.metric(f"Óbitos em {ano_selecionado}", f"{obitos_no_ano:,}")
st.divider()

# --- Abas de Navegação ---
tab_mapa, tab_pop, tab_san, tab_pob, tab_mor = st.tabs(["📍 Mapa Interativo", "👤 População", "💧 Saneamento", "⚖️ Pobreza", "❤️ Mortalidade"])

with tab_mapa:
    st.header("Análise Geográfica por Bairro")
    dado_para_mostrar = st.selectbox(
        "Selecione o indicador para visualizar no mapa:",
        ('Índice de Risco (Exemplo)', 'População (Exemplo)')
    )
    coluna_cor = 'indice_risco' if dado_para_mostrar == 'Índice de Risco (Exemplo)' else 'populacao'
    escala_cor = 'Reds' if dado_para_mostrar == 'Índice de Risco (Exemplo)' else 'Blues'

    if geojson and not df_bairros.empty:
        fig = px.choropleth_mapbox(
            df_bairros, geojson=geojson, locations='nome',
            featureidkey="properties.NOME", color=coluna_cor,
            color_continuous_scale=escala_cor, mapbox_style="carto-positron",
            zoom=11, center={"lat": -21.1775, "lon": -47.8100},
            opacity=0.7, labels={'indice_risco': 'Índice de Risco', 'populacao': 'População'},
            hover_data={'nome': True, 'indice_risco': True, 'populacao': True}
        )
        fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível carregar o mapa.")

with tab_pop:
    # ... (código da aba População)
    st.header("População por sexo")
    pop_total = df_demografia['populacao'].sum()
    pop_masc = df_demografia[df_demografia['sexo'] == 'Masculino']['populacao'].sum()
    pop_fem = df_demografia[df_demografia['sexo'] == 'Feminino']['populacao'].sum()
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("População Geral", f"{pop_total:,}")
    col_b.metric("População Masculina", f"{pop_masc:,}")
    col_c.metric("População Feminina", f"{pop_fem:,}")
    st.subheader("População por cor ou raça")
    sexo_grafico = st.radio("Filtrar gráfico por Sexo:", ['Ambos', 'Masculino', 'Feminino'], horizontal=True)
    df_demografia_filtrado = df_demografia.copy()
    if sexo_grafico != 'Ambos':
        df_demografia_filtrado = df_demografia[df_demografia['sexo'] == sexo_grafico]
    fig_pop_raca = px.bar(df_demografia_filtrado, x='raca', y='populacao', color='sexo', text_auto=True, barmode='group')
    st.plotly_chart(fig_pop_raca, use_container_width=True)


with tab_san:
    # ... (código da aba Saneamento)
    st.header("Condições de Saneamento nos Domicílios")
    col1, col2, col3 = st.columns(3)
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

with tab_pob:
    # ... (código da aba Pobreza)
    st.header("Indicadores de Pobreza e Desigualdade")
    st.markdown("Os gráficos mostram a média e o intervalo de confiança (limite inferior e superior) para cada indicador.")
    df_pobreza_fmt = df_pobreza.copy()
    df_pobreza_fmt['indicador'] = df_pobreza_fmt['indicador'].str.replace('Incidência da pobreza subjetiva', 'Pobreza Subjetiva').str.replace('Incidência da pobreza', 'Pobreza')
    fig_pobreza = px.bar(df_pobreza_fmt, x='indicador', y='media', error_y=df_pobreza_fmt['limite_superior'] - df_pobreza_fmt['media'], error_y_minus=df_pobreza_fmt['media'] - df_pobreza_fmt['limite_inferior'], title='Indicadores com Intervalo de Confiança', labels={'indicador': 'Indicador', 'media': 'Valor (em % para Pobreza)'}, text_auto='.2f')
    st.plotly_chart(fig_pobreza, use_container_width=True)

with tab_mor:
    # ... (código da aba Mortalidade)
    st.header(f"Análise de Mortalidade ({ano_selecionado})")
    df_causas_filtrado = df_mortalidade_causas[df_mortalidade_causas['ano'] == ano_selecionado]
    df_causas_top = df_causas_filtrado.nlargest(10, 'obitos')
    fig_morte = px.bar(df_causas_top.sort_values('obitos'), x='obitos', y='causa', orientation='h', text='obitos', title=f"Principais Causas de Morte em {ano_selecionado}")
    st.plotly_chart(fig_morte, use_container_width=True)
