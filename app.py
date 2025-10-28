import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(layout="wide", page_title="Ribeirão em Dados", page_icon="🦟")

# --- CSS PARA ESTILIZAÇÃO ---
def load_css(theme):
    light_theme = """
    <style>
        .kpi-card {
            border-radius: 10px; padding: 15px 20px; text-align: center;
            border: 1px solid #e0e0e0; transition: all 0.3s ease-in-out;
        }
        .kpi-card:hover { box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border: 1px solid #1f77b4; }
        .kpi-card h3 { font-size: 16px; color: #666; margin-bottom: 5px; font-weight: 500; }
        .kpi-card p { font-size: 28px; font-weight: bold; color: #1f77b4; }
        .kpi-card .delta-p { font-size: 14px; color: #2ca02c; } /* Verde para positivo/melhora */
        .kpi-card .delta-n { font-size: 14px; color: #d62728; } /* Vermelho para negativo/piora */
    </style>
    """
    dark_theme = """
    <style>
        .stApp { background-color: #0E1117; color: #fafafa; }
        .kpi-card {
            background-color: #1C2129; border: 1px solid #2D343E;
            border-radius: 10px; padding: 15px 20px; text-align: center;
        }
        .kpi-card h3 { color: #a0a0a0; }
        .kpi-card p { color: #1f77b4; }
        .kpi-card .delta-p { color: #2ca02c; }
        .kpi-card .delta-n { color: #d62728; }
        [data-testid="stSidebar"] { background-color: #1C2129; }
    </style>
    """
    st.markdown(dark_theme if theme == 'Escuro' else light_theme, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

@st.cache_data
def carregar_dados_locais():
    if not os.path.exists(DB_PATH):
        st.error(f"Erro: Banco de dados '{DB_FILE}' não encontrado! Execute 'db_local.py' primeiro.")
        st.stop()
    conn = sqlite3.connect(DB_PATH)
    query_regioes = """
    SELECT 
        cr.ano, cr.nome_regiao, cr.casos, rd.populacao, rd.densidade_pop, 
        rd.renda_media, rd.risco_socioambiental, rd.latitude, rd.longitude
    FROM casos_dengue_regiao_anual cr
    JOIN regioes_dados rd ON cr.nome_regiao = rd.nome_regiao
    """
    tabelas = {
        'df_regioes': pd.read_sql_query(query_regioes, conn),
        'df_mensal': pd.read_sql_query("SELECT * FROM casos_dengue_mensal", conn),
        'df_perfil': pd.read_sql_query("SELECT * FROM perfil_dengue_anual", conn),
        'df_municipio': pd.read_sql_query("SELECT * FROM dados_municipio", conn),
        'df_obitos_gerais': pd.read_sql_query("SELECT * FROM obitos_gerais_anual", conn),
    }
    conn.close()
    return tabelas

# --- PREPARAÇÃO DOS DADOS E FILTROS ---
dados = carregar_dados_locais()
df_regioes = dados['df_regioes']
df_mensal = dados['df_mensal']
df_perfil = dados['df_perfil']
df_municipio = dados['df_municipio']
df_obitos_gerais = dados['df_obitos_gerais']

st.sidebar.title("Filtros e Opções")
anos_disponiveis = ["Todos os Anos"] + sorted(df_regioes['ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", options=anos_disponiveis)
tema = st.sidebar.radio("Selecione o Tema", ('Claro', 'Escuro'))
load_css(tema) # Carrega o CSS com base na seleção

# --- LÓGICA DE FILTRAGEM ---
if ano_selecionado == "Todos os Anos":
    periodo_titulo = "2020-2024"
    df_perfil_filtrado = df_perfil.sum().to_frame().T
    df_mensal_filtrado = df_mensal.groupby('mes')['casos'].sum().reset_index()
    df_regioes_filtrado = df_regioes.groupby('nome_regiao').agg({
        'casos': 'sum', 'populacao': 'first', 'densidade_pop': 'first', 
        'renda_media': 'first', 'risco_socioambiental': 'first',
        'latitude': 'first', 'longitude': 'first'
    }).reset_index()
    obitos_gerais_filtrado = df_obitos_gerais['obitos_total'].sum()
else:
    periodo_titulo = str(ano_selecionado)
    df_perfil_filtrado = df_perfil[df_perfil['ano'] == ano_selecionado].copy()
    df_mensal_filtrado = df_mensal[df_mensal['ano'] == ano_selecionado].copy()
    df_regioes_filtrado = df_regioes[df_regioes['ano'] == ano_selecionado].copy()
    # Tratamento seguro para pegar o valor de óbitos gerais
    obitos_ano_df = df_obitos_gerais[df_obitos_gerais['ano'] == ano_selecionado]
    obitos_gerais_filtrado = obitos_ano_df['obitos_total'].iloc[0] if not obitos_ano_df.empty else "N/A"

# --- TÍTULO E KPIs ---
st.title(f"🦟 Ribeirão em Dados")

# KPIs de População (só aparecem na visão geral)
if ano_selecionado == "Todos os Anos":
    st.subheader("Dados Demográficos e Socioeconômicos")
    pop_censo = df_municipio[df_municipio['indicador'] == 'População Censo 2022']['valor'].iloc[0]
    pop_estimada = df_municipio[df_municipio['indicador'] == 'População Estimada 2025']['valor'].iloc[0]
    densidade = df_municipio[df_municipio['indicador'] == 'Densidade Demográfica 2022']['valor'].iloc[0]

    col_pop1, col_pop2, col_pop3 = st.columns(3)
    with col_pop1:
        st.markdown(f'<div class="kpi-card"><h3>População (Censo 2022)</h3><p>{int(pop_censo):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
    with col_pop2:
        st.markdown(f'<div class="kpi-card"><h3>População (Estimada 2025)</h3><p>{int(pop_estimada):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
    with col_pop3:
        st.markdown(f'<div class="kpi-card"><h3>Densidade Demográfica</h3><p>{densidade:,.2f} hab/km²</p></div>'.replace(",", "."), unsafe_allow_html=True)
    st.divider()

st.subheader(f"Panorama da Dengue: {periodo_titulo}")
total_casos = df_perfil_filtrado['casos_total'].iloc[0]
total_curados = df_perfil_filtrado['curados'].iloc[0]
total_obitos_dengue = df_perfil_filtrado['obitos_dengue'].iloc[0]
delta_casos_text = ""

if ano_selecionado != "Todos os Anos":
    ano_anterior = ano_selecionado - 1
    if ano_anterior in df_perfil['ano'].values:
        total_casos_anterior = df_perfil[df_perfil['ano'] == ano_anterior]['casos_total'].iloc[0]
        if total_casos_anterior > 0:
            delta_casos = ((total_casos - total_casos_anterior) / total_casos_anterior * 100)
            delta_class = "delta-p" if delta_casos < 0 else "delta-n" # P = positivo(melhora), N = negativo(piora)
            delta_casos_text = f'<div class="{delta_class}">{delta_casos:+.1f}% vs {ano_anterior}</div>'

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.markdown(f'<div class="kpi-card"><h3>Total de Casos</h3><p>{int(total_casos):,}</p>{delta_casos_text}</div>'.replace(",", "."), unsafe_allow_html=True)
with col_kpi2:
    st.markdown(f'<div class="kpi-card"><h3>Pacientes Curados</h3><p>{int(total_curados):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
with col_kpi3:
    st.markdown(f'<div class="kpi-card"><h3>Óbitos por Dengue</h3><p>{int(total_obitos_dengue)}</p></div>', unsafe_allow_html=True)
with col_kpi4:
    obitos_gerais_display = f"{int(obitos_gerais_filtrado):,}".replace(",", ".") if isinstance(obitos_gerais_filtrado, (int, float)) else obitos_gerais_filtrado
    st.markdown(f'<div class="kpi-card"><h3>Óbitos Gerais (Cidade)</h3><p>{obitos_gerais_display}</p></div>', unsafe_allow_html=True)


# --- ABAS DE NAVEGAÇÃO ---
tabs_list = ["🗺️ Análise Geográfica", "📈 Análise Temporal e de Perfil", "🔬 Análise de Correlação"]
if ano_selecionado == "Todos os Anos":
    tabs_list.insert(0, "📄 RESUMO")

tabs = st.tabs(tabs_list)
tab_offset = 1 if ano_selecionado == "Todos os Anos" else 0

if ano_selecionado == "Todos os Anos":
    with tabs[0]:
        st.header("Resumo dos Principais Insights (2020-2024)")
        st.info("Esta aba apresenta os destaques encontrados na análise de todo o período. Utilize o filtro na barra lateral para detalhar um ano específico.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Evolução Anual de Casos")
            df_casos_anuais = df_perfil.groupby('ano')['casos_total'].sum().reset_index()
            fig_evolucao_anual = px.bar(df_casos_anuais, x='ano', y='casos_total', text_auto=True, title="Total de Casos de Dengue por Ano")
            st.plotly_chart(fig_evolucao_anual, use_container_width=True)
        with col2:
            st.subheader("Distribuição de Casos por Região")
            df_casos_totais_regiao = df_regioes.groupby('nome_regiao')['casos'].sum().reset_index()
            fig_regiao_total = px.pie(df_casos_totais_regiao, names='nome_regiao', values='casos', title="Concentração de Casos por Região (Total)", hole=0.4)
            st.plotly_chart(fig_regiao_total, use_container_width=True)

with tabs[tab_offset]:
    st.header(f"Análise Geográfica por Regiões")
    st.info("""
    Este mapa interativo mostra a distribuição da Dengue em Ribeirão Preto por macrorregião.
    - **Tamanho das Bolhas:** Indica o **Total de Casos** na região. Quanto maior a bolha, mais casos.
    - **Cor das Bolhas:** Indica o **Número de Óbitos** por Dengue (estimado). Quanto mais vermelha, mais óbitos.
    Passe o mouse sobre as bolhas para ver os detalhes de cada região.
    """)
    
    df_regioes_filtrado['obitos_estimados'] = (total_obitos_dengue * (df_regioes_filtrado['casos'] / total_casos)).clip(lower=0).round() if total_casos > 0 else 0

    fig_map = px.scatter_map(df_regioes_filtrado, 
        lat="latitude", lon="longitude",
        size="casos",         # Tamanho da bolha pelo número de casos
        color="obitos_estimados",  # Cor da bolha pelo número de óbitos
        hover_name="nome_regiao",
        hover_data={"casos": True, "obitos_estimados": True, "latitude": False, "longitude": False},
        color_continuous_scale=px.colors.sequential.Reds,
        size_max=50,
        zoom=10.5,
        map_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='Óbitos')
    st.plotly_chart(fig_map, use_container_width=True)

with tabs[tab_offset + 1]:
    st.header("Análise Temporal e de Perfil")
    st.info("""
    Esta seção detalha como a dengue se comportou ao longo do tempo (sazonalidade) e qual perfil demográfico foi mais afetado.
    - **Gráfico de Barras:** Mostra os meses com maior número de casos, evidenciando os períodos de maior transmissão.
    - **Gráfico de Pizza:** Apresenta a proporção de casos entre os sexos masculino e feminino.
    """)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("**Evolução dos Casos por Mês**")
        mapa_meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        df_mensal_filtrado['mes_nome'] = df_mensal_filtrado['mes'].map(mapa_meses)
        fig_bar = px.bar(df_mensal_filtrado.sort_values('mes'), y='mes_nome', x='casos', orientation='h', text_auto=True)
        fig_bar.update_layout(yaxis_title="Mês", xaxis_title="Número de Casos", yaxis={'categoryorder':'array', 'categoryarray': list(mapa_meses.values())})
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.write("**Distribuição por Sexo**")
        df_sexo = df_perfil_filtrado[['casos_masculino', 'casos_feminino']].T.reset_index()
        df_sexo.columns = ['sexo', 'casos']
        df_sexo['sexo'] = df_sexo['sexo'].str.replace('casos_', '').str.capitalize()
        fig_pie = px.pie(df_sexo, names='sexo', values='casos', hole=0.4,
                         color='sexo', color_discrete_map={'Masculino':'#1f77b4', 'Feminino':'#9467bd'})
        st.plotly_chart(fig_pie, use_container_width=True)

with tabs[tab_offset + 2]:
    st.header("Análise de Correlação")
    st.info("""
    **Como funciona esta análise?** Este gráfico é a principal ferramenta para responder à nossa pergunta de pesquisa. Ele permite cruzar a **Taxa de Incidência de Dengue** com diferentes fatores de risco simulados para cada região.
    - **Selecione um Fator de Risco:** Use o menu abaixo para escolher qual fator você quer analisar (Renda, Densidade, etc.).
    - **Interprete o Gráfico:** Cada bolha é uma macrorregião. Se as bolhas formarem um padrão (uma "linha" imaginária), há uma correlação.
        - **Padrão Ascendente (↗):** Sugere que, quanto maior o fator de risco, maior a incidência de dengue.
        - **Padrão Descendente (↘):** Sugere que, quanto maior o fator (ex: renda), menor a incidência de dengue.
    """)
    df_regioes_filtrado['taxa_incidencia'] = (df_regioes_filtrado['casos'] / df_regioes_filtrado['populacao'] * 100000)
    eixo_x_selecionado = st.selectbox(
        "Selecione o Fator de Risco (Eixo X):",
        options=['risco_socioambiental', 'densidade_pop', 'renda_media']
    )
    labels_eixos = {'risco_socioambiental': 'Índice de Risco Socioambiental (Simulado)', 'densidade_pop': 'Densidade Populacional (hab/km²)', 'renda_media': 'Renda Média (R$)'}
    
    fig_scatter = px.scatter(
        df_regioes_filtrado, x=eixo_x_selecionado, y='taxa_incidencia',
        size='populacao', color='nome_regiao', hover_name='nome_regiao', size_max=60,
        labels={'taxa_incidencia': 'Incidência / 100 mil hab.', eixo_x_selecionado: labels_eixos[eixo_x_selecionado]}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

