import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(layout="wide", page_title="Ribeirão em Dados", page_icon="🦟")

# --- CSS PARA ESTILIZAÇÃO (TEMA CLARO FIXO) ---
def load_css():
    """Aplica o CSS para o tema claro e estiliza os cartões KPI."""
    light_theme = """
    <style>
        .kpi-card {
            border-radius: 10px; padding: 15px 20px; text-align: center;
            border: 1px solid #e0e0e0; transition: all 0.3s ease-in-out;
            background-color: #f8f8f8;
        }
        .kpi-card:hover { box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border: 1px solid #1f77b4; }
        .kpi-card h3 { font-size: 16px; color: #666; margin-bottom: 5px; font-weight: 500; }
        .kpi-card p { font-size: 28px; font-weight: bold; color: #1f77b4; }
    </style>
    """
    st.markdown(light_theme, unsafe_allow_html=True)

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

# 1. Definir a lista de páginas (base para a navegação lateral)
tabs_list_base = ["🗺️ Análise Geográfica", "📈 Análise Temporal e de Perfil", "🔬 Análise de Correlação"]

st.sidebar.title("Selecione o ano de análise")
anos_disponiveis = ["Todos os Anos"] + sorted(df_regioes['ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox(" ", options=anos_disponiveis)

# Lógica para adicionar o RESUMO
tabs_list_final = tabs_list_base.copy()
if ano_selecionado == "Todos os Anos":
    tabs_list_final.insert(0, "📄 RESUMO")
    
load_css()

st.sidebar.markdown("---")
st.sidebar.header("Páginas do Dashboard")
# 2. Usa st.sidebar.radio para simular a navegação por abas
pagina_selecionada = st.sidebar.radio(
    "Navegação:",
    options=tabs_list_final,
    index=0 # Inicia na primeira opção
)

# --- LÓGICA DE FILTRAGEM ---
if ano_selecionado == "Todos os Anos":
    periodo_titulo = f"{df_regioes['ano'].min()}-{df_regioes['ano'].max()}"
    df_perfil_filtrado = df_perfil.sum(numeric_only=True).to_frame().T
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

# KPIs da Dengue (Usando st.metric para melhor UX e limpeza de código)
# --- TÍTULO E KPIs ---
# ... (Seu código de KPIs Demográficos - não alterado) ...

# KPIs da Dengue (Usando st.metric para melhor UX e limpeza de código)
st.subheader(f"Panorama da Dengue: {periodo_titulo}")
total_casos = df_perfil_filtrado['casos_total'].iloc[0]
total_curados = df_perfil_filtrado['curados'].iloc[0]
total_obitos_dengue = df_perfil_filtrado['obitos_dengue'].iloc[0]

# --- CORREÇÃO: Inicializar as variáveis de delta ---
delta_casos_valor = None
delta_casos_cor = "normal" # Valor padrão seguro

if ano_selecionado != "Todos os Anos":
    ano_anterior = ano_selecionado - 1
    if ano_anterior in df_perfil['ano'].values:
        total_casos_anterior = df_perfil[df_perfil['ano'] == ano_anterior]['casos_total'].iloc[0]
        # Garantia contra divisão por zero
        if total_casos_anterior > 0:
            delta_casos = total_casos - total_casos_anterior
            # Se o aumento de casos é ruim, o delta deve ser "inverse" (vermelho) quando delta é positivo
            delta_casos_cor = "inverse" if delta_casos > 0 else "normal"
            delta_casos_valor = f"{delta_casos:+,}".replace(",", ".")
        else:
            # Se o ano anterior tinha 0 casos, mostrar o total atual
            delta_casos_valor = f"+{total_casos:,}".replace(",", ".")
            delta_casos_cor = "inverse"


col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.metric(label="Total de Casos", value=f"{int(total_casos):,}".replace(",", "."), 
              delta=delta_casos_valor, delta_color=delta_casos_cor)
with col_kpi2:
    st.metric(label="Pacientes Curados", value=f"{int(total_curados):,}".replace(",", "."))
with col_kpi3:
    st.metric(label="Óbitos por Dengue", value=f"{int(total_obitos_dengue)}")
with col_kpi4:
    obitos_gerais_display = f"{int(obitos_gerais_filtrado):,}".replace(",", ".") if isinstance(obitos_gerais_filtrado, (int, float)) else obitos_gerais_filtrado
    st.metric(label="Óbitos Gerais (Cidade)", value=obitos_gerais_display)

# --- CONTEÚDO PRINCIPAL (BASEADO NA SELEÇÃO DA SIDEBAR) ---

if pagina_selecionada == "📄 RESUMO":
    # --- CONTEÚDO DA ABA RESUMO (só aparece em "Todos os Anos") ---
    if ano_selecionado == "Todos os Anos":
        st.header("Resumo dos Principais Insights (2020-2024)")
        st.info("Esta seção apresenta os destaques encontrados na análise de todo o período. Navegue pelas páginas laterais para os detalhes.")
        
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

elif pagina_selecionada == "🗺️ Análise Geográfica":
    # --- CONTEÚDO DA ABA ANÁLISE GEOGRÁFICA (COM SELETOR DE COR) ---
    st.header(f"🗺️ Análise Geográfica por Regiões: {periodo_titulo}")

    df_regioes_filtrado['taxa_incidencia'] = (df_regioes_filtrado['casos'] / df_regioes_filtrado['populacao'] * 100000)
    df_regioes_filtrado['obitos_estimados'] = (total_obitos_dengue * (df_regioes_filtrado['casos'] / total_casos)).clip(lower=0).round() if total_casos > 0 else 0

    map_color_var = st.selectbox(
        "Selecione o que Mapear nas CORES das regiões:",
        options=['taxa_incidencia', 'risco_socioambiental', 'renda_media', 'populacao'],
        format_func=lambda x: {'taxa_incidencia': 'Taxa de Incidência de Dengue', 'risco_socioambiental': 'Índice de Risco Socioambiental', 'renda_media': 'Renda Média', 'populacao': 'População'}[x]
    )
    
    # Configuração de cor (Reds para variáveis de risco/incidência)
    color_scale = px.colors.sequential.Reds if map_color_var in ['risco_socioambiental', 'taxa_incidencia'] else px.colors.sequential.Plasma
        
    st.info(f"""
    Este mapa mostra a distribuição espacial. 
    - **Tamanho da bolha:** Proporcional ao **Total de Casos**.
    - **Cor da bolha:** Proporcional à **{map_color_var.replace('_', ' ').title()}** na região.
    """)
    

    fig_map = px.scatter_map(df_regioes_filtrado, 
        lat="latitude", lon="longitude",
        size="casos", 
        color=map_color_var, # Variável de cor dinâmica
        hover_name="nome_regiao",
        hover_data={"casos": True, map_color_var: ':.2f', "latitude": False, "longitude": False},
        color_continuous_scale=color_scale,
        size_max=50,
        zoom=10.5,
        map_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text=map_color_var.replace('_', ' ').title())
    st.plotly_chart(fig_map, use_container_width=True)

elif pagina_selecionada == "📈 Análise Temporal e de Perfil":
    # --- CONTEÚDO DA ABA ANÁLISE TEMPORAL E DE PERFIL ---
    st.header("Análise Temporal e de Perfil")
    st.info("""
    Esta seção detalha como a dengue se comportou ao longo do tempo (sazonalidade) e qual perfil demográfico foi mais afetado.
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

elif pagina_selecionada == "🔬 Análise de Correlação":
    # --- CONTEÚDO DA ABA ANÁLISE DE CORRELAÇÃO (COM MÉTRICAS E OLS) ---
    st.header("🔬 Análise de Correlação: Risco Socioambiental vs. Dengue")
    
    st.info("""
    **Objetivo:** Cruzar a **Taxa de Incidência de Dengue** com fatores socioambientais (risco, densidade, renda) por região para encontrar relações.
    """)
    
    df_regioes_filtrado['taxa_incidencia'] = (df_regioes_filtrado['casos'] / df_regioes_filtrado['populacao'] * 100000)
    
    # 1. Filtro do Eixo X
    eixo_x_selecionado = st.selectbox(
        "Selecione o Fator de Risco (Eixo X):",
        options=['risco_socioambiental', 'densidade_pop', 'renda_media']
    )
    labels_eixos = {
        'risco_socioambiental': 'Índice de Risco Socioambiental (0-1.0)', 
        'densidade_pop': 'Densidade Populacional (hab/km²)', 
        'renda_media': 'Renda Média (R$)'
    }
    
    # 2. Cálculo do Coeficiente de Correlação de Pearson (r)
    if len(df_regioes_filtrado) > 1 and df_regioes_filtrado[eixo_x_selecionado].nunique() > 1:
        try:
            corr_coef = df_regioes_filtrado['taxa_incidencia'].corr(df_regioes_filtrado[eixo_x_selecionado])
        except Exception:
            corr_coef = 0.0

        # 3. Interpretação 
        if corr_coef >= 0.7: intensidade = "MUITO FORTE e POSITIVA"
        elif corr_coef >= 0.4: intensidade = "MODERADA e POSITIVA"
        elif corr_coef > -0.4 and corr_coef < 0.4: intensidade = "FRACA ou Inexistente"
        elif corr_coef <= -0.7: intensidade = "MUITO FORTE e NEGATIVA"
        else: intensidade = "MODERADA e NEGATIVA"

        # Exibir o Coeficiente e a Interpretação em um box de destaque
        col_c1, col_c2 = st.columns([1, 3])
        with col_c1:
            st.metric(label=f"Coeficiente de Correlação ($r$)", value=f"{corr_coef:.2f}")
        with col_c2:
            st.success(f"**Conclusão Estatística:** Correlação **{intensidade}**. Um $r$ próximo de $\pm 1$ indica forte alinhamento.")
            
        # 4. Gráfico de Dispersão com Linha de Tendência (OLS)
        st.markdown("##### Gráfico de Dispersão (Taxa de Incidência vs. Fator de Risco)")
        
        fig_scatter = px.scatter(
            df_regioes_filtrado, x=eixo_x_selecionado, y='taxa_incidencia',
            size='populacao', color='nome_regiao', hover_name='nome_regiao', size_max=60,
            labels={'taxa_incidencia': 'Incidência de Dengue / 100 mil hab.', eixo_x_selecionado: labels_eixos[eixo_x_selecionado]},
            trendline='ols', # Linha de Regressão OLS
            template='plotly_white'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        st.warning("Não é possível calcular a correlação: Dados insuficientes para o ano/filtro selecionado ou poucas regiões com valores diferentes.")

    # 5. Tabela de Ranking
    st.markdown("---")
    st.subheader("Ranking de Regiões por Risco e Incidência")
    df_ranking = df_regioes_filtrado[['nome_regiao', 'taxa_incidencia', eixo_x_selecionado]].sort_values('taxa_incidencia', ascending=False)
    df_ranking.columns = ['Região', 'Incidência / 100 mil hab.', labels_eixos[eixo_x_selecionado]]
    st.dataframe(df_ranking, use_container_width=True, hide_index=True, 
                 column_config={"Incidência / 100 mil hab.": st.column_config.NumberColumn(format="%.0f")})