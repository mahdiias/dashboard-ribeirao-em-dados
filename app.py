import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(layout="wide", page_title="Ribeirão em Dados", page_icon="🦟")


def load_css(theme):
    light_theme = """
    <style>
        .kpi-card {
            border-radius: 10px; padding: 15px 10px; text-align: center;
            border: 1px solid #e0e0e0; transition: all 0.3s ease-in-out;
            background-color: #f8f8f8;
            height: 100%;
        }
        .kpi-card:hover { box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border: 1px solid #1f77b4; }
        .kpi-card h3 { font-size: 14px; color: #666; margin-bottom: 5px; font-weight: 500; }
        .kpi-card p { font-size: 24px; font-weight: bold; margin: 0; } 
        
        /* Cores dos KPIs (Nova Estilização) */
        .kpi-notif p { color: #1f77b4; } /* Azul - Notificações */
        .kpi-curados p { color: #2ca02c; } /* Verde - Curados */
        .kpi-obitos p { color: #d62728; } /* Vermelho - Óbitos Dengue */
        .kpi-outros p { color: #ff7f0e; } /* Laranja - Outros Óbitos */
        .kpi-neutro p { color: #7f7f7f; } /* Cinza - Sem Desfecho */

        .explanation-box {
            background-color: #e8f4f8; border-left: 5px solid #1f77b4;
            padding: 20px; margin-bottom: 20px; border-radius: 5px;
            font-size: 16px; 
        }
    </style>
    """
    st.markdown(light_theme, unsafe_allow_html=True)

# define o caminho do banco de dados
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

# funcao para conectar no banco e carregar os dados
@st.cache_data
def carregar_dados_locais():
    # verifica se o banco existe
    if not os.path.exists(DB_PATH):
        st.error(f"Erro: Banco de dados '{DB_FILE}' não encontrado! Execute 'db_local.py' primeiro.")
        st.stop()
    conn = sqlite3.connect(DB_PATH)
    
    # query principal que cruza dados de dengue com censo e geometria (join)
    query_regioes = """
    SELECT 
        cr.ano, cr.nome_regiao, cr.casos,
        geo.latitude, geo.longitude,
        c22.total_populacao, c22.populacao_por_km2 as densidade_pop,
        c10.renda_per_capita, c10.populacao_negra_pct, c10.anos_de_estudo
    FROM casos_dengue_regiao_anual cr
    LEFT JOIN regioes_geometria geo ON cr.nome_regiao = geo.nome_regiao
    LEFT JOIN censo_2022 c22 ON cr.nome_regiao = c22.regiao
    LEFT JOIN censo_2010 c10 ON cr.nome_regiao = c10.regiao
    """
    
    # carrega as tabelas do banco para dataframes do pandas
    tabelas = {
        'df_regioes': pd.read_sql_query(query_regioes, conn),
        'df_mensal': pd.read_sql_query("SELECT * FROM casos_dengue_mensal", conn),
        'df_perfil': pd.read_sql_query("SELECT * FROM perfil_dengue_anual", conn),
        'df_municipio': pd.read_sql_query("SELECT * FROM dados_municipio", conn),
        'df_obitos_gerais': pd.read_sql_query("SELECT * FROM obitos_gerais_anual", conn),
        'df_faixa': pd.read_sql_query("SELECT * FROM dengue_faixa_etaria", conn)
    }
    conn.close()
    return tabelas

# executa a funcao de carga
dados = carregar_dados_locais()
df_regioes = dados['df_regioes']
df_mensal = dados['df_mensal']
df_perfil = dados['df_perfil']
df_municipio = dados['df_municipio']
df_obitos_gerais = dados['df_obitos_gerais']
df_faixa = dados['df_faixa']

st.sidebar.title("Painel de Controle")
# cria lista de anos disponiveis para o filtro
anos_disponiveis = ["Todos os Anos"] + sorted(df_regioes['ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o ano de análise", options=anos_disponiveis)

# define as abas de navegacao
tabs_list_base = ["🗺️ Análise Geográfica", "📈 Análise Temporal e de Perfil", "📈 Análise Temporal de Óbitos", "🔬 Análise de Correlação"]
tabs_list_final = tabs_list_base.copy()
# se selecionar todos os anos adiciona a aba de resumo
if ano_selecionado == "Todos os Anos":
    tabs_list_final.insert(0, "📄 RESUMO")
    
load_css(None) 

st.sidebar.markdown("---")
st.sidebar.header("Navegação")
pagina_selecionada = st.sidebar.radio("Ir para:", options=tabs_list_final, index=0)

# caixa expansivel com as fontes de dados na lateral
with st.sidebar.expander("📚 Fontes de Dados", expanded=False):
    st.markdown("""
    <small>
    **Dados Epidemiológicos (Dengue):**
    * Min. da Saúde/SVSA - Sinan Net e DataSUS
    
    **Dados Demográficos e Sociais:**
    * IBGE - Censo 2022 
    * IBGE - Censo 2010 
    * Sposito e Catalão 
    
    **Outros:**
    * Coordenadas Geográficas: Elaboração Própria
    </small>
    """, unsafe_allow_html=True)

if ano_selecionado == "Todos os Anos":
    periodo_titulo = f"{df_regioes['ano'].min()}-{df_regioes['ano'].max()}"
    # soma os dados numericos para ter o total do periodo
    df_perfil_filtrado = df_perfil.sum(numeric_only=True).to_frame().T
    df_mensal_filtrado = df_mensal.groupby('mes')['casos'].sum().reset_index()
    df_faixa_filtrada = df_faixa.sum(numeric_only=True).to_frame().T
    
  
    df_regioes_filtrado = df_regioes.groupby('nome_regiao').agg({
        'casos': 'sum', 'total_populacao': 'first', 'densidade_pop': 'first', 
        'renda_per_capita': 'first', 'populacao_negra_pct': 'first', 'anos_de_estudo': 'first',
        'latitude': 'first', 'longitude': 'first'
    }).reset_index()
    
    obitos_gerais_filtrado = df_obitos_gerais['obitos_total'].sum()
else:
    periodo_titulo = str(ano_selecionado)
    df_perfil_filtrado = df_perfil[df_perfil['ano'] == ano_selecionado].copy()
    df_mensal_filtrado = df_mensal[df_mensal['ano'] == ano_selecionado].copy()
    df_regioes_filtrado = df_regioes[df_regioes['ano'] == ano_selecionado].copy()
    df_faixa_filtrada = df_faixa[df_faixa['ano'] == ano_selecionado].copy()
    
    obitos_ano_df = df_obitos_gerais[df_obitos_gerais['ano'] == ano_selecionado]
    obitos_gerais_filtrado = obitos_ano_df['obitos_total'].iloc[0] if not obitos_ano_df.empty else "N/A"

# calculo da taxa de incidencia (casos divididos por populacao vezes 100 mil)
df_regioes_filtrado['taxa_incidencia'] = (df_regioes_filtrado['casos'] / df_regioes_filtrado['total_populacao'] * 100000)

st.title(f"🦟 Ribeirão em Dados: Monitoramento da Dengue")


def plot_desfechos():
    total_curados = df_perfil_filtrado['curados'].iloc[0]
    total_obitos_dengue = df_perfil_filtrado['obitos_dengue'].iloc[0]
    total_obitos_outros = df_perfil_filtrado['obitos_outras_causas'].iloc[0]
    em_investigacao = df_perfil_filtrado['obitos_investigacao'].iloc[0]
    ign_branco = df_perfil_filtrado['ign_branco'].iloc[0]
    
    dados = {
        'Situação': ['Cura', 'Óbito Dengue', 'Óbito Outras', 'Em Investigação', 'Ign/Branco'],
        'Quantidade': [total_curados, total_obitos_dengue, total_obitos_outros, em_investigacao, ign_branco]
    }
    
    cores = {'Cura': '#2ca02c', 'Óbito Dengue': '#d62728', 'Óbito Outras': '#ff7f0e', 'Em Investigação': '#7f7f7f', 'Ign/Branco': '#bcbd22'}
    
    fig = px.bar(pd.DataFrame(dados), x='Quantidade', y='Situação', orientation='h', text_auto=True, 
                  title="Matemática dos Desfechos (Status Final)", color='Situação',
                  color_discrete_map=cores)
    fig.update_layout(showlegend=False)
    return fig


if pagina_selecionada == "📄 RESUMO":
    if ano_selecionado == "Todos os Anos":
        st.header("📄 Resumo e Análise de casos totais")
        
        
        st.markdown("""
        <div class="explanation-box">
            <b>O que é este Painel?</b><br>
            Uma ferramenta de inteligência epidemiológica que analisa a Dengue em Ribeirão Preto, cruzando dados de Saúde com dados Socioeconômicos e Demográficos.
            <br><br>
            <b>Objetivo:</b>Este painel busca entender se há correlação entre a incidência de casos de Dengue por bairros de Ribeirão Preto e a presença de fatores de risco socioambientais, como a existência de terrenos baldios, pontos de descarte irregular de lixo e a densidade populacional nos últimos 5 anos.
        </div>
        """, unsafe_allow_html=True)
        
        
        st.subheader("Dados Demográficos (Contexto da Cidade)")
        pop_censo = df_municipio[df_municipio['indicador'] == 'População Censo 2022']['valor'].iloc[0]
        pop_estimada = df_municipio[df_municipio['indicador'] == 'População Estimada 2025']['valor'].iloc[0]
        densidade = df_municipio[df_municipio['indicador'] == 'Densidade Demográfica 2022']['valor'].iloc[0]

        col_pop1, col_pop2, col_pop3 = st.columns(3)
        with col_pop1: 
            st.markdown(f'<div class="kpi-card" style="border-left: 5px solid #1f77b4;"><h3>População (Censo 2022)</h3><p style="color:#1f77b4">{int(pop_censo):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
        with col_pop2: 
            st.markdown(f'<div class="kpi-card" style="border-left: 5px solid #ff7f0e;"><h3>População (Estimada 2025)</h3><p style="color:#ff7f0e">{int(pop_estimada):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
        with col_pop3: 
            st.markdown(f'<div class="kpi-card" style="border-left: 5px solid #2ca02c;"><h3>Densidade Demográfica</h3><p style="color:#2ca02c">{densidade:,.2f} hab/km²</p></div>'.replace(",", "."), unsafe_allow_html=True)
        st.divider()

        st.subheader(f"Panorama da Dengue: {periodo_titulo}")

        total_casos = df_perfil_filtrado['casos_total'].iloc[0]
        total_curados = df_perfil_filtrado['curados'].iloc[0]
        total_obitos_dengue = df_perfil_filtrado['obitos_dengue'].iloc[0]
        total_obitos_outros = df_perfil_filtrado['obitos_outras_causas'].iloc[0]
        ign_branco = df_perfil_filtrado['ign_branco'].iloc[0]
        em_investigacao = df_perfil_filtrado['obitos_investigacao'].iloc[0]
        total_sem_desfecho = ign_branco + em_investigacao

        delta_casos_text = ""
        if ano_selecionado != "Todos os Anos":
            pass

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(f'<div class="kpi-card kpi-notif"><h3>Notificações da Doença</h3><p>{int(total_casos):,}</p>{delta_casos_text}</div>'.replace(",", "."), unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="kpi-card kpi-curados"><h3>Curados</h3><p>{int(total_curados):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="kpi-card kpi-obitos"><h3>Óbitos (Dengue)</h3><p>{int(total_obitos_dengue)}</p></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="kpi-card kpi-outros"><h3>Óbitos (Outros*)</h3><p>{int(total_obitos_outros)}</p></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="kpi-card kpi-neutro"><h3>Sem Desfecho**</h3><p>{int(total_sem_desfecho):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)

        st.caption("*Óbitos de pacientes com dengue confirmados por outras causas. **Soma de Ignorados/Brancos e Óbitos em Investigação.")
        st.markdown("---")
        
        
        st.subheader("1. Histórico Anual de Casos (Tendência)")
        df_hist = df_perfil.groupby('ano')['casos_total'].sum().reset_index()
        
        fig_hist = px.line(
            df_hist, 
            x='ano', 
            y='casos_total', 
            text='casos_total',
            title="Evolução do Total de Notificações (2020-2024)",
            markers=True,
            color_discrete_sequence=['#1f77b4'] 
        )

        fig_hist.update_traces(
        textposition="top center", 
        texttemplate='%{text:,.0f}', 
        marker=dict(size=12) 
        )
        fig_hist.update_layout(
        xaxis=dict(tickmode='linear', title=dict(text="Ano", font=dict(size=18))), 
        yaxis=dict(title=dict(text="Número de Casos", font=dict(size=18))), 
        title=dict(font=dict(size=22)), 
        font=dict(size=16), 
        height=500
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        with st.expander("Análise dos Extremos: Por que a queda em 2021 e o pico em 2024?"):
            st.markdown("""A variação extrema de casos entre os anos pode ser explicada por fatores **epidemiológicos e climáticos**:
    
        Queda em 2021 (481 casos):*Principalmente devido à **imunidade populacional** (após o surto de 2020) e ao impacto das medidas de **distanciamento social** e restrições impostas pela pandemia de COVID-19, que indiretamente limitaram a circulação do vírus.
    
        Pico em 2024 (46.531 casos):** Impulsionado pela **reintrodução de novos sorotipos** do vírus (contra os quais a população não tinha defesa) e por **condições climáticas extremas** (altas temperaturas e chuvas irregulares), que favorecem a proliferação acelerada do mosquito *Aedes aegypti*.
        """)
        st.markdown("---")
        
    st.subheader("2. Incidência Regional (Visualização do Risco Socioeconômico)")
    st.info("⚠️ **IMPORTANTE:**O gráfico foi dividido em duas partes. A Região Leste foi separada devido ao seu pico extremo, que ofuscava a análise das demais regiões. A Região Leste apresenta uma Taxa de Incidência **muito superior** (aprox. 55.236 / 100k) em relação às demais, sendo o **principal motor** da correlação negativa observada.Esta concentração massiva de casos pode ser um **artefato de classificação/geocodificação** na fonte de dados, onde grande parte dos casos da cidade foram atribuídos a esta macrorregião por padrão. Analisamos o ranking das demais regiões separadamente para maior clareza." )

    df_leste = df_regioes_filtrado[df_regioes_filtrado['nome_regiao'] == 'Leste'].copy()
    df_outras_regioes = df_regioes_filtrado[df_regioes_filtrado['nome_regiao'] != 'Leste'].copy()

    st.markdown("#### A) Foco no Extremo (Região Leste)")
    col_le, col_avg = st.columns([2, 1])

    with col_le:
        incidencia_media_cidade = df_regioes_filtrado['taxa_incidencia'].mean()
        df_leste_vs_media = pd.DataFrame({
            'Região': ['Leste', 'Média da Cidade'],
            'Incidência': [df_leste['taxa_incidencia'].iloc[0], incidencia_media_cidade],
            'Cor': ['Leste', 'Média']
        })
        
        fig_leste = px.bar(
            df_leste_vs_media, 
            x='Incidência', 
            y='Região', 
            orientation='h', 
            text='Incidência',
            title=f"Leste (Extremo) vs. Média Geral ({incidencia_media_cidade:,.0f}/100k)",
            color='Região',
            color_discrete_map={'Leste': '#d62728', 'Média da Cidade': '#7f7f7f'}
        )
        fig_leste.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_leste.update_layout(xaxis_title="Incidência / 100 mil hab.", yaxis_title="")
        st.plotly_chart(fig_leste, use_container_width=True)

    st.markdown("#### B) Ranking de Risco e Renda (Demais Regiões)")
    st.caption("Observamos que a Região Centro, com renda média/baixa, apresenta a maior incidência, alinhando-se à correlação negativa esperada.No entanto, a Região Norte, a mais pobre de todas, registra a incidência mínima. Este contraste sugere que a incidência da Dengue é um fenômeno multifatorial. Fatores como a Densidade Populacional (muito alta no Centro) ou a circulação viral específica do período podem ter um peso maior na determinação do risco do que a renda isoladamente.")

    df_risco_rank = df_outras_regioes.sort_values('taxa_incidencia', ascending=True)

    fig_risco = px.bar(
        df_risco_rank,
        x='taxa_incidencia', 
        y='nome_regiao',
        orientation='h',
        text=df_risco_rank['taxa_incidencia'].round(0).astype(int),
        title="Correlação: Incidência x Renda (Exceto Leste)",
        color='renda_per_capita', 
        color_continuous_scale=px.colors.sequential.Inferno_r, # Renda Baixa = Cor Quente
    )
    fig_risco.update_layout(
        yaxis={'categoryorder':'total ascending', 'title': "Região"}, 
        xaxis={'title': "Incidência / 100 mil hab."},
        coloraxis_colorbar=dict(title="Renda Média (R$)"),
        height=450 
    ) 
    fig_risco.update_traces(textposition='outside')
    st.plotly_chart(fig_risco, use_container_width=True)
    
# pagina de analise geografica (mapa) 
elif pagina_selecionada == "🗺️ Análise Geográfica":
    # [Mantido o código da Análise Geográfica]
    st.header(f"🗺️ Análise Geográfica por Regiões")
    
    st.markdown("""
    <div class="explanation-box">
        <b>Objetivo:</b> Identificar onde a doença está mais concentrada.<br>
        <b>Metodologia:</b> Cruzamos as notificações georreferenciadas por bairro (agrupadas em regiões) com a população do Censo 2022.<br>
        <b>Cálculos:</b>
        <ul>
            <li><b>Taxa de Incidência:</b> (Casos ÷ População) × 100.000. É a medida padrão da OMS para comparar regiões de tamanhos diferentes.</li>
            <li><b>Cor:</b> Representa a intensidade do indicador (ex: áreas mais pobres em amarelo/verde, áreas com mais dengue em vermelho).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # opcoes do seletor de cores do mapa
    opcoes_cor = {
        'taxa_incidencia': 'Taxa de Incidência (Casos/100k)',
        'renda_per_capita': 'Renda Média (R$)',
        'populacao_negra_pct': '% População Negra',
        'anos_de_estudo': 'Escolaridade Média (Anos)'
    }

    map_color_var = st.selectbox("Colorir mapa por:", list(opcoes_cor.keys()), format_func=lambda x: opcoes_cor[x])
    
    # define a escala de cor (verde/azul para social, vermelho para doenca)
    if map_color_var in ['renda_per_capita', 'anos_de_estudo']:
        scale = px.colors.sequential.Viridis
    else:
        scale = px.colors.sequential.Reds
        
    # plota o mapa de bolhas
    fig_map = px.scatter_map(df_regioes_filtrado, 
        lat="latitude", lon="longitude",
        size="casos", color=map_color_var,
        hover_name="nome_regiao",
        hover_data={"casos": True, "taxa_incidencia": ":.0f", map_color_var: ':.2f'},
        color_continuous_scale=scale, size_max=50, zoom=10.5, map_style="carto-positron"
    )
    # garante tamanho minimo da bolha para nao sumir
    fig_map.update_traces(marker=dict(sizemin=8))
    st.plotly_chart(fig_map, use_container_width=True)

# pagina de analise temporal e perfil - MANTER CÓDIGO AQUI
elif pagina_selecionada == "📈 Análise Temporal e de Perfil":
    st.header("Análise Temporal e de Perfil")
    
    st.markdown("""
    <div class="explanation-box">
        <b>Objetivo:</b> Entender <i>QUANDO</i> (sazonalidade) e <i>QUEM</i> (perfil demográfico) adoece.<br>
        <b>Dados Usados:</b> Campos de 'Data de Notificação', 'Sexo' e 'Idade' das fichas do SINAN.<br>
        <b>Importância:</b> Ajuda a planejar campanhas sazonais (ex: reforço antes de Março) e focar em grupos de risco.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Sazonalidade (Meses de Pico)")
        mapa_meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        df_mensal_filtrado['mes_nome'] = df_mensal_filtrado['mes'].map(mapa_meses)
        fig_bar = px.bar(df_mensal_filtrado.sort_values('mes'), y='mes_nome', x='casos', orientation='h', text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.subheader("Distribuição por Sexo")
        df_sexo = df_perfil_filtrado[['casos_masculino', 'casos_feminino']].T.reset_index()
        df_sexo.columns = ['sexo', 'casos']
        df_sexo['sexo'] = df_sexo['sexo'].str.replace('casos_', '').str.capitalize()
        fig_pie = px.pie(df_sexo, names='sexo', values='casos', hole=0.4, color_discrete_sequence=['#1f77b4', '#e377c2'])
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.subheader("Faixa Etária e Desfechos")
    c_age, c_outcome = st.columns(2)
    with c_age:
        if not df_faixa_filtrada.empty:
            df_faixa_long = df_faixa_filtrada.drop(columns=['ano'], errors='ignore').melt(var_name='Faixa', value_name='Casos')
            df_faixa_long['Faixa'] = df_faixa_long['Faixa'].str.replace('casos_', '').str.replace('_', ' ').str.title()
            fig_age = px.bar(df_faixa_long, x='Casos', y='Faixa', orientation='h', text_auto=True, title="Casos por Idade")
            st.plotly_chart(fig_age, use_container_width=True)
    with c_outcome:
        st.plotly_chart(plot_desfechos(), use_container_width=True)

# pagina de analise temporal de óbitos - MANTER CÓDIGO AQUI
elif pagina_selecionada == "📈 Análise Temporal de Óbitos":
    st.header("Análise Temporal de Óbitos")
    st.markdown("""
    <div class="explanation-box">
        <b>Sobre esta aba:</b><br>
        Apresenta uma visão de óbitos de todo o período. Útil para gestores entenderem a tendência histórica.
    </div>
    """, unsafe_allow_html=True)
    st.subheader("Histórico Anual de Óbitos por Dengue")
    df_hist = df_perfil.groupby('ano')['obitos_dengue'].sum().reset_index()
    fig = px.bar(df_hist, x='ano', y='obitos_dengue', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Histórico Anual de Óbitos por Outras Causas")
        df_hist = df_perfil.groupby('ano')['obitos_outras_causas'].sum().reset_index()
        fig = px.bar(df_hist, x='ano', y='obitos_outras_causas', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Histórico Anual de Óbitos em Investigação")
        df_hist = df_perfil.groupby('ano')['obitos_investigacao'].sum().reset_index()
        fig = px.bar(df_hist, x='ano', y='obitos_investigacao', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

# pagina de correlacao (estudo ecologico) - MANTER CÓDIGO AQUI
elif pagina_selecionada == "🔬 Análise de Correlação":
    st.header("🔬 Laboratório de Correlação (Estudo Ecológico)")
    
    st.markdown("""
    <div class="explanation-box">
        <b>O que é esta análise?</b><br>
        Um estudo ecológico que busca associações estatísticas entre o ambiente (bairro) e a doença.<br>
        <b>Metodologia:</b> Calculamos o Coeficiente de Pearson (r).<br>
        <b>Como interpretar:</b>
        <ul>
            <li><b>Matriz (Heatmap):</b> Cores quentes (azul) indicam que os dados "andam juntos" (ex: Mais Chuva = Mais Dengue). Cores frias (vermelho) indicam o oposto.</li>
            <li><b>Gráfico de Dispersão (Regressão):</b> Cada ponto é uma região. A linha mostra a tendência. Se a linha sobe, a correlação é positiva.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    cols_analise = {
        'taxa_incidencia': 'Incidência Dengue',
        'renda_per_capita': 'Renda Média',
        'populacao_negra_pct': '% Pop. Negra',
        'anos_de_estudo': 'Escolaridade',
        'densidade_pop': 'Densidade Pop.'
    }
    
    st.subheader("1. Matriz de Correlação (Visão Geral) (2020 - 2024)")
    # calcula a correlacao e renomeia colunas
    df_corr = df_regioes_filtrado.copy()
    
    # Substituir np.nan por 0 na densidade populacional antes de calcular a correlação
    # df_corr['densidade_pop'] = df_corr['densidade_pop'].fillna(0)
    
    df_corr = df_corr[list(cols_analise.keys())].rename(columns=cols_analise).corr()
    # plota o heatmap
    fig_heat = px.imshow(df_corr, text_auto=".2f", color_continuous_scale='RdBu_r', zmin=-1, zmax=1, aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()
    
    st.subheader("2. Detalhe da Regressão (Teste de Hipótese) (2020 - 2024)")
    eixo_x_selecionado = st.selectbox("Escolha o Fator Social (Eixo X):", options=['renda_per_capita', 'populacao_negra_pct', 'anos_de_estudo', 'densidade_pop'], format_func=lambda x: cols_analise[x])
    
    if len(df_regioes_filtrado) > 1:
        # calcula o coeficiente r de pearson
        r = df_regioes_filtrado['taxa_incidencia'].corr(df_regioes_filtrado[eixo_x_selecionado])
        st.metric("Coeficiente Pearson (r)", f"{r:.2f}")
        
        # plota grafico de dispersao com linha de tendencia (ols)
        fig_scatter = px.scatter(
            df_regioes_filtrado, x=eixo_x_selecionado, y='taxa_incidencia',
            size='total_populacao', color='nome_regiao', hover_name='nome_regiao', size_max=60,
            trendline='ols',
            labels={'taxa_incidencia': 'Incidência (Casos/100k)', eixo_x_selecionado: cols_analise[eixo_x_selecionado]}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Dados insuficientes para gerar regressão.")

    st.markdown("---")
    st.subheader("Tabela de Dados por Região (2020 - 2024)")
    df_ranking = df_regioes_filtrado[['nome_regiao', 'taxa_incidencia', eixo_x_selecionado]].sort_values('taxa_incidencia', ascending=False)
    df_ranking.columns = ['Região', 'Incidência / 100 mil hab.', cols_analise[eixo_x_selecionado]]
    st.dataframe(df_ranking, use_container_width=True, hide_index=True, column_config={"Incidência / 100 mil hab.": st.column_config.NumberColumn(format="%.0f")})