import sqlite3
import os
import random

# Define o nome e o caminho do arquivo do banco de dados
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

def criar_e_popular_banco():
    """
    Cria e popula o banco de dados SQLite com dados tratados de 2020-2024,
    incluindo dados gerais de óbitos e a simulação de dados socioeconômicos por macrorregião.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Tabela 1: DADOS GERAIS DO MUNICÍPIO ---
    cursor.execute("""
    CREATE TABLE dados_municipio (
        indicador TEXT UNIQUE, valor REAL, unidade TEXT
    )""")
    # Fonte: dados gerais ribeirão preto.xlsx e PDF
    dados_gerais = [
        ('População Censo 2022', 698642, 'pessoas'),
        ('População Estimada 2025', 731639, 'pessoas'),
        ('Área Territorial', 650.916, 'km²'),
        ('Densidade Demográfica 2022', 1073.32, 'hab/km²'),
        ('PIB per capita 2021', 55484.91, 'R$')
    ]
    cursor.executemany("INSERT INTO dados_municipio (indicador, valor, unidade) VALUES (?, ?, ?)", dados_gerais)

    # --- Tabela 2: CASOS DE DENGUE POR ANO E MÊS (2020-2024) ---
    cursor.execute("CREATE TABLE casos_dengue_mensal (ano INTEGER, mes INTEGER, casos INTEGER)")
    dados_mensais = [
        (2020, 1, 3043), (2020, 2, 6860), (2020, 3, 5153), (2020, 4, 1929), (2020, 5, 873), (2020, 6, 195), (2020, 7, 65), (2020, 8, 25), (2020, 9, 20), (2020, 10, 12), (2020, 11, 16), (2020, 12, 9),
        (2021, 1, 42), (2021, 2, 55), (2021, 3, 65), (2021, 4, 109), (2021, 5, 77), (2021, 6, 25), (2021, 7, 19), (2021, 8, 12), (2021, 9, 10), (2021, 10, 16), (2021, 11, 21), (2021, 12, 30),
        (2022, 1, 68), (2022, 2, 222), (2022, 3, 1103), (2022, 4, 2692), (2022, 5, 2415), (2022, 6, 948), (2022, 7, 282), (2022, 8, 154), (2022, 9, 110), (2022, 10, 100), (2022, 11, 90), (2022, 12, 100),
        (2023, 1, 471), (2023, 2, 991), (2023, 3, 2686), (2023, 4, 3885), (2023, 5, 2694), (2023, 6, 1140), (2023, 7, 439), (2023, 8, 230), (2023, 9, 185), (2023, 10, 198), (2023, 11, 245), (2023, 12, 142),
        (2024, 1, 1046), (2024, 2, 4821), (2024, 3, 15438), (2024, 4, 16999), (2024, 5, 8227)
    ]
    cursor.executemany("INSERT INTO casos_dengue_mensal (ano, mes, casos) VALUES (?, ?, ?)", dados_mensais)

    # --- Tabela 3: PERFIL ANUAL DA DENGUE (2020-2024) ---
    cursor.execute("""
    CREATE TABLE perfil_dengue_anual (
        ano INTEGER UNIQUE, casos_total INTEGER, casos_masculino INTEGER, 
        casos_feminino INTEGER, curados INTEGER, obitos_dengue INTEGER
    )""")
    dados_perfil = [
        (2020, 18200, 8273, 9896, 17395, 10), (2021, 481, 222, 259, 345, 1),
        (2022, 8284, 3892, 4391, 7586, 2), (2023, 13306, 6279, 7023, 12413, 10),
        (2024, 46531, 21038, 25483, 44246, 32)
    ]
    cursor.executemany("INSERT INTO perfil_dengue_anual (ano, casos_total, casos_masculino, casos_feminino, curados, obitos_dengue) VALUES (?, ?, ?, ?, ?, ?)", dados_perfil)
    
    # --- Tabela 4: ÓBITOS GERAIS DO MUNICÍPIO (2020-2022) ---
    cursor.execute("CREATE TABLE obitos_gerais_anual (ano INTEGER UNIQUE, obitos_total INTEGER)")
    # Fonte: Dados_ribeirao_preto.xlsx - Mortalidade.csv
    dados_obitos_gerais = [(2020, 5484), (2021, 6555), (2022, 5499)]
    cursor.executemany("INSERT INTO obitos_gerais_anual (ano, obitos_total) VALUES (?, ?)", dados_obitos_gerais)

    # --- Tabela 5: DADOS SOCIOECONÔMICOS E DE RISCO POR REGIÃO (SIMULADO) ---
    cursor.execute("""
    CREATE TABLE regioes_dados (
        nome_regiao TEXT UNIQUE, populacao INTEGER, densidade_pop REAL, 
        renda_media REAL, risco_socioambiental REAL, latitude REAL, longitude REAL
    )""")
    regioes = [
        ("Norte", 150000, 8500.5, 1800.75, 0.8, -21.14, -47.82),
        ("Sudeste", 120000, 6500.8, 4200.90, 0.3, -21.18, -47.78),
        ("Sul", 100000, 4500.1, 6500.00, 0.1, -21.22, -47.80),
        ("Centro-Oeste", 180000, 7800.7, 2300.10, 0.7, -21.18, -47.85),
        ("Nordeste", 100000, 9500.0, 2100.00, 0.6, -21.16, -47.79)
    ]
    cursor.executemany("INSERT INTO regioes_dados (nome_regiao, populacao, densidade_pop, renda_media, risco_socioambiental, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?)", regioes)

    # --- Tabela 6: CASOS DE DENGUE POR REGIÃO E ANO (2020-2024) ---
    cursor.execute("CREATE TABLE casos_dengue_regiao_anual (ano INTEGER, nome_regiao TEXT, casos INTEGER)")
    dados_regiao = [
        (2020, 'Norte', 1), (2021, 'Norte', 2), (2022, 'Norte', 1), (2023, 'Norte', 4), (2024, 'Norte', 3),
        (2020, 'Nordeste', 1), (2021, 'Nordeste', 0), (2022, 'Nordeste', 5), (2023, 'Nordeste', 5), (2024, 'Nordeste', 11),
        (2020, 'Sudeste', 18189), (2021, 'Sudeste', 475), (2022, 'Sudeste', 8267), (2023, 'Sudeste', 13280), (2024, 'Sudeste', 46482),
        (2020, 'Sul', 3), (2021, 'Sul', 1), (2022, 'Sul', 5), (2023, 'Sul', 10), (2024, 'Sul', 17),
        (2020, 'Centro-Oeste', 6), (2021, 'Centro-Oeste', 3), (2022, 'Centro-Oeste', 6), (2023, 'Centro-Oeste', 7), (2024, 'Centro-Oeste', 18)
    ]
    cursor.executemany("INSERT INTO casos_dengue_regiao_anual (ano, nome_regiao, casos) VALUES (?, ? ,?)", dados_regiao)

    print("Todas as tabelas foram criadas e populadas com sucesso.")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    criar_e_popular_banco()