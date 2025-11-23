import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# configuracao da pagina e titulo da aba do navegador
st.set_page_config(layout="wide", page_title="Ribeirão em Dados", page_icon="🦟")

# funcao para carregar o estilo css visual dos cartoes e caixas
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
        .kpi-card p { font-size: 24px; font-weight: bold; color: #1f77b4; margin: 0; }
        .kpi-card .delta-p { font-size: 12px; color: #2ca02c; } 
        .kpi-card .delta-n { font-size: 12px; color: #d62728; }
        .explanation-box {
            background-color: #e8f4f8; border-left: 5px solid #1f77b4;
            padding: 15px; margin-bottom: 20px; border-radius: 5px;
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

# --- barra lateral (sidebar) ---
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
    
# carrega o css
load_css(None) 

st.sidebar.markdown("---")
st.sidebar.header("Navegação")
# menu de radio para trocar de pagina
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

# --- logica de filtragem dos dados ---
if ano_selecionado == "Todos os Anos":
    periodo_titulo = f"{df_regioes['ano'].min()}-{df_regioes['ano'].max()}"
    # soma os dados numericos para ter o total do periodo
    df_perfil_filtrado = df_perfil.sum(numeric_only=True).to_frame().T
    df_mensal_filtrado = df_mensal.groupby('mes')['casos'].sum().reset_index()
    df_faixa_filtrada = df_faixa.sum(numeric_only=True).to_frame().T
    
    # agrupa por regiao somando casos e mantendo dados de censo (first)
    df_regioes_filtrado = df_regioes.groupby('nome_regiao').agg({
        'casos': 'sum', 'total_populacao': 'first', 'densidade_pop': 'first', 
        'renda_per_capita': 'first', 'populacao_negra_pct': 'first', 'anos_de_estudo': 'first',
        'latitude': 'first', 'longitude': 'first'
    }).reset_index()
    
    obitos_gerais_filtrado = df_obitos_gerais['obitos_total'].sum()
else:
    # filtra os dataframes pelo ano especifico selecionado
    periodo_titulo = str(ano_selecionado)
    df_perfil_filtrado = df_perfil[df_perfil['ano'] == ano_selecionado].copy()
    df_mensal_filtrado = df_mensal[df_mensal['ano'] == ano_selecionado].copy()
    df_regioes_filtrado = df_regioes[df_regioes['ano'] == ano_selecionado].copy()
    df_faixa_filtrada = df_faixa[df_faixa['ano'] == ano_selecionado].copy()
    
    obitos_ano_df = df_obitos_gerais[df_obitos_gerais['ano'] == ano_selecionado]
    obitos_gerais_filtrado = obitos_ano_df['obitos_total'].iloc[0] if not obitos_ano_df.empty else "N/A"

# calculo da taxa de incidencia (casos divididos por populacao vezes 100 mil)
df_regioes_filtrado['taxa_incidencia'] = (df_regioes_filtrado['casos'] / df_regioes_filtrado['total_populacao'] * 100000)

# --- titulo principal e kpis ---
st.title(f"🦟 Ribeirão em Dados: Monitoramento da Dengue")

# exibe dados demograficos apenas na visao geral
if ano_selecionado == "Todos os Anos":
    st.markdown("""
    <div class="explanation-box">
        <b>O que é este painel?</b><br>
        Uma ferramenta de inteligência epidemiológica que cruza dados de saúde (SINAN) com dados sociodemográficos (Censo IBGE).
        O objetivo é entender não apenas <i>quantos</i> casos ocorreram, mas <i>onde</i> e <i>quais fatores sociais</i> podem estar relacionados.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Dados Demográficos (Contexto da Cidade)")
    pop_censo = df_municipio[df_municipio['indicador'] == 'População Censo 2022']['valor'].iloc[0]
    pop_estimada = df_municipio[df_municipio['indicador'] == 'População Estimada 2025']['valor'].iloc[0]
    densidade = df_municipio[df_municipio['indicador'] == 'Densidade Demográfica 2022']['valor'].iloc[0]

    c_pop1, c_pop2, c_pop3 = st.columns(3)
    with c_pop1: st.markdown(f'<div class="kpi-card"><h3>População (Censo 2022)</h3><p>{int(pop_censo):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
    with c_pop2: st.markdown(f'<div class="kpi-card"><h3>População (Estimada 2025)</h3><p>{int(pop_estimada):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
    with c_pop3: st.markdown(f'<div class="kpi-card"><h3>Densidade Demográfica</h3><p>{densidade:,.2f} hab/km²</p></div>'.replace(",", "."), unsafe_allow_html=True)
    st.divider()

# kpis epidemiologicos principais
st.subheader(f"Panorama da Dengue: {periodo_titulo}")

# extrai valores para os cartoes
total_casos = df_perfil_filtrado['casos_total'].iloc[0]
total_curados = df_perfil_filtrado['curados'].iloc[0]
total_obitos_dengue = df_perfil_filtrado['obitos_dengue'].iloc[0]
total_obitos_outros = df_perfil_filtrado['obitos_outras_causas'].iloc[0]
# calcula sem desfecho somando ignorados e investigacao
ign_branco = df_perfil_filtrado['ign_branco'].iloc[0]
em_investigacao = df_perfil_filtrado['obitos_investigacao'].iloc[0]
total_sem_desfecho = ign_branco + em_investigacao

# logica do delta comparando com ano anterior
delta_casos_text = ""
if ano_selecionado != "Todos os Anos":
    ano_ant = ano_selecionado - 1
    if ano_ant in df_perfil['ano'].values:
        total_ant = df_perfil[df_perfil['ano'] == ano_ant]['casos_total'].iloc[0]
        if total_ant > 0:
            delta = ((total_casos - total_ant) / total_ant * 100)
            d_class = "delta-p" if delta < 0 else "delta-n"
            delta_casos_text = f'<div class="{d_class}">{delta:+.1f}% vs {ano_ant}</div>'

# exibe os 5 cartoes de kpi lado a lado
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.markdown(f'<div class="kpi-card"><h3>Notificações</h3><p>{int(total_casos):,}</p>{delta_casos_text}</div>'.replace(",", "."), unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi-card"><h3>Curados</h3><p>{int(total_curados):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi-card"><h3>Óbitos (Dengue)</h3><p style="color:#d62728">{int(total_obitos_dengue)}</p></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="kpi-card"><h3>Óbitos (Outros*)</h3><p style="color:#ff7f0e">{int(total_obitos_outros)}</p></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="kpi-card"><h3>Sem Desfecho**</h3><p style="color:#7f7f7f">{int(total_sem_desfecho):,}</p></div>'.replace(",", "."), unsafe_allow_html=True)

st.caption("*Óbitos de pacientes com dengue confirmados por outras causas. **Soma de Ignorados/Brancos e Óbitos em Investigação.")

# funcao auxiliar para gerar o grafico de desfechos
def plot_desfechos():
    dados = {
        'Situação': ['Cura', 'Óbito Dengue', 'Óbito Outras', 'Em Investigação', 'Ign/Branco'],
        'Quantidade': [total_curados, total_obitos_dengue, total_obitos_outros, em_investigacao, ign_branco]
    }
    fig = px.bar(pd.DataFrame(dados), x='Quantidade', y='Situação', orientation='h', text_auto=True, 
                 title="Matemática dos Desfechos (Status Final)", color='Situação',
                 color_discrete_map={'Cura': '#2ca02c', 'Óbito Dengue': '#d62728', 'Óbito Outras': '#ff7f0e', 'Em Investigação': '#7f7f7f', 'Ign/Branco': '#bcbd22'})
    fig.update_layout(showlegend=False)
    return fig

# --- renderizacao das paginas ---

# pagina de resumo (so aparece se todos os anos selecionado)
if pagina_selecionada == "📄 RESUMO":
    if ano_selecionado == "Todos os Anos":
        st.header("Resumo Executivo")
        st.markdown("""
        <div class="explanation-box">
            <b>Sobre esta aba:</b><br>
            Apresenta uma visão consolidada de todo o período. Útil para gestores entenderem a tendência histórica e a eficiência do tratamento (desfechos).
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Histórico Anual")
            df_hist = df_perfil.groupby('ano')['casos_total'].sum().reset_index()
            fig = px.bar(df_hist, x='ano', y='casos_total', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Distribuição Regional")
            df_pie = df_regioes_filtrado.groupby('nome_regiao')['casos'].sum().reset_index()
            fig_p = px.pie(df_pie, names='nome_regiao', values='casos', hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)

# pagina de analise geografica (mapa)
elif pagina_selecionada == "🗺️ Análise Geográfica":
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
    if map_color_var in ['renda_per_capita', 'anos_de_estudo', 'taxa_incidencia', 'populacao_negra_pct']:
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

# pagina de analise temporal e perfil
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

# pagina de analise temporal de óbitos
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

# pagina de correlacao (estudo ecologico)
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
    
    st.subheader("1. Matriz de Correlação (Visão Geral)")
    # calcula a correlacao e renomeia colunas
    df_corr = df_regioes_filtrado[list(cols_analise.keys())].rename(columns=cols_analise).corr()
    # plota o heatmap
    fig_heat = px.imshow(df_corr, text_auto=".2f", color_continuous_scale='RdBu_r', zmin=-1, zmax=1, aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()
    
    st.subheader("2. Detalhe da Regressão (Teste de Hipótese)")
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
    st.subheader("Tabela de Dados por Região")
    df_ranking = df_regioes_filtrado[['nome_regiao', 'taxa_incidencia', eixo_x_selecionado]].sort_values('taxa_incidencia', ascending=False)
    df_ranking.columns = ['Região', 'Incidência / 100 mil hab.', cols_analise[eixo_x_selecionado]]
    st.dataframe(df_ranking, use_container_width=True, hide_index=True, column_config={"Incidência / 100 mil hab.": st.column_config.NumberColumn(format="%.0f")})