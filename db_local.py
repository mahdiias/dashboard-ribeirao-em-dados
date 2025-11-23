import sqlite3
import os

# --- CONFIGURAÇÕES INICIAIS ---
DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

def criar_e_popular_banco():
    """
    Cria e popula o banco de dados SQLite com dados oficiais de Ribeirão Preto (2020-2024).
    
    Atualizações:
    - Dados de óbitos detalhados (Dengue vs Outras Causas) conforme SINAN/CSV.
    - Inclusão da coluna 'ign_branco' para fechar o total de notificações.
    - Remoção de dados socioeconômicos simulados (agora usa Censo 2010/2022).
    """
    
    # Garante que o diretório existe e remove banco antigo para recriar do zero
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Iniciando criação do banco de dados...")

    # ---------------------------------------------------------
    # TABELA 1: DADOS GERAIS DO MUNICÍPIO
    # ---------------------------------------------------------
    cursor.execute("CREATE TABLE dados_municipio (indicador TEXT UNIQUE, valor REAL, unidade TEXT)")
    dados_gerais = [
        ('População Censo 2022', 698642, 'pessoas'),
        ('População Estimada 2025', 731639, 'pessoas'),
        ('Área Territorial', 650.916, 'km²'),
        ('Densidade Demográfica 2022', 1073.32, 'hab/km²'),
        ('PIB per capita 2021', 55484.91, 'R$')
    ]
    cursor.executemany("INSERT INTO dados_municipio VALUES (?, ?, ?)", dados_gerais)

    # ---------------------------------------------------------
    # TABELA 2: CASOS MENSAIS (Série Histórica)
    # ---------------------------------------------------------
    cursor.execute("CREATE TABLE casos_dengue_mensal (ano INTEGER, mes INTEGER, casos INTEGER)")
    dados_mensais = [
        (2020, 1, 3043), (2020, 2, 6860), (2020, 3, 5153), (2020, 4, 1929), (2020, 5, 873), (2020, 6, 195), (2020, 7, 65), (2020, 8, 25), (2020, 9, 20), (2020, 10, 12), (2020, 11, 16), (2020, 12, 9),
        (2021, 1, 42), (2021, 2, 55), (2021, 3, 65), (2021, 4, 109), (2021, 5, 77), (2021, 6, 25), (2021, 7, 19), (2021, 8, 12), (2021, 9, 10), (2021, 10, 16), (2021, 11, 21), (2021, 12, 30),
        (2022, 1, 68), (2022, 2, 222), (2022, 3, 1103), (2022, 4, 2692), (2022, 5, 2415), (2022, 6, 948), (2022, 7, 282), (2022, 8, 154), (2022, 9, 110), (2022, 10, 100), (2022, 11, 90), (2022, 12, 100),
        (2023, 1, 471), (2023, 2, 991), (2023, 3, 2686), (2023, 4, 3885), (2023, 5, 2882), (2023, 6, 724), (2023, 7, 164), (2023, 8, 125), (2023, 9, 116), (2023, 10, 167), (2023, 11, 345), (2023, 12, 750),
        (2024, 1, 3171), (2024, 2, 6644), (2024, 3, 9456), (2024, 4, 10172), (2024, 5, 8824), (2024, 6, 3536), (2024, 7, 1359), (2024, 8, 644), (2024, 9, 420), (2024, 10, 519), (2024, 11, 722), (2024, 12, 1064)
    ]
    cursor.executemany("INSERT INTO casos_dengue_mensal VALUES (?, ?, ?)", dados_mensais)

    # ---------------------------------------------------------
    # TABELA 3: PERFIL ANUAL E DESFECHOS (ATUALIZADO)
    # Fonte: CSV 'dados dengue obito.csv'
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE perfil_dengue_anual (
        ano INTEGER UNIQUE, 
        casos_total INTEGER, 
        casos_masculino INTEGER, 
        casos_feminino INTEGER, 
        curados INTEGER,
        ign_branco INTEGER, -- Coluna adicionada para bater o total
        obitos_dengue INTEGER,
        obitos_outras_causas INTEGER,
        obitos_investigacao INTEGER
    )""")
    
    # Dados exatos do CSV oficial (incluindo Ign/Branco):
    dados_perfil = [
        # Ano, Total, Masc, Fem, Curados, Ign/Branco, Óbitos Dengue, Ób. Outras, Ób. Inv
        (2020, 18200, 8273, 9896, 17395, 789, 10, 5, 1),
        (2021, 481, 222, 259, 345, 133, 1, 2, 0),
        (2022, 8284, 3892, 4391, 7586, 692, 2, 4, 0),
        (2023, 13306, 6279, 7023, 12413, 877, 10, 4, 2),
        (2024, 46531, 21038, 25483, 44246, 2239, 32, 12, 2)
    ]
    cursor.executemany("INSERT INTO perfil_dengue_anual VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", dados_perfil)

    # ---------------------------------------------------------
    # TABELA 4: ÓBITOS GERAIS (Mortalidade Geral da Cidade)
    # ---------------------------------------------------------
    cursor.execute("CREATE TABLE obitos_gerais_anual (ano INTEGER UNIQUE, obitos_total INTEGER)")
    dados_obitos_gerais = [(2020, 5484), (2021, 6555), (2022, 5499)]
    cursor.executemany("INSERT INTO obitos_gerais_anual VALUES (?, ?)", dados_obitos_gerais)

    # ---------------------------------------------------------
    # TABELA 5: GEOMETRIA DAS REGIÕES (Lat/Lon)
    # ---------------------------------------------------------
    cursor.execute("CREATE TABLE regioes_geometria (nome_regiao TEXT UNIQUE, latitude REAL, longitude REAL)")
    regioes_geo = [
        ('Norte', -21.128794, -47.798842),
        ('Leste', -21.184219, -47.757172),
        ('Sul', -21.219751, -47.802107),
        ('Oeste', -21.174825, -47.834542),
        ('Centro', -21.180012, -47.812378)
    ]
    cursor.executemany("INSERT INTO regioes_geometria VALUES (?, ?, ?)", regioes_geo)

    # ---------------------------------------------------------
    # TABELA 6: CASOS POR REGIÃO (Anual)
    # ---------------------------------------------------------
    cursor.execute("CREATE TABLE casos_dengue_regiao_anual (ano INTEGER, nome_regiao TEXT, casos INTEGER)")
    dados_regiao = [
        (2020, 'Norte', 1), (2021, 'Norte', 2), (2022, 'Norte', 1), (2023, 'Norte', 4), (2024, 'Norte', 3),
        (2020, 'Leste', 18189), (2021, 'Leste', 475), (2022, 'Leste', 8267), (2023, 'Leste', 13280), (2024, 'Leste', 46482),
        (2020, 'Sul', 3), (2021, 'Sul', 1), (2022, 'Sul', 5), (2023, 'Sul', 10), (2024, 'Sul', 17),
        (2020, 'Oeste', 6), (2021, 'Oeste', 3), (2022, 'Oeste', 6), (2023, 'Oeste', 7), (2024, 'Oeste', 18),
        (2020, 'Centro', 1), (2021, 'Centro', 0), (2022, 'Centro', 5), (2023, 'Centro', 5), (2024, 'Centro', 11)
    ]
    cursor.executemany("INSERT INTO casos_dengue_regiao_anual VALUES (?, ?, ?)", dados_regiao)

    # ---------------------------------------------------------
    # TABELA 7: CENSO 2022 (Dados Reais)
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE censo_2022 (
        regiao TEXT, area REAL, total_populacao INTEGER, 
        populacao_por_km2 REAL, total_domicilios INTEGER
    )""")
    dados_censo_2022 = [
        ('Norte', 104.79, 212992, 2032.49, 90881),
        ('Leste', 112.82, 156951, 1391.09, 75244),
        ('Sul', 118.61, 93285, 786.48, 50131),
        ('Oeste', 91.43, 187748, 2053.27, 80630),
        ('Centro', 2.17, 14890, 6840.61, 10705)
    ]
    cursor.executemany("INSERT INTO censo_2022 VALUES (?, ?, ?, ?, ?)", dados_censo_2022)

    # ---------------------------------------------------------
    # TABELA 8: CENSO 2010 (Dados Socioeconômicos Reais)
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE censo_2010 (
        regiao TEXT, renda_per_capita REAL, 
        populacao_negra_pct REAL, anos_de_estudo REAL
    )""")
    dados_censo_2010 = [
        ('Norte', 563, 5.84, 5.5),
        ('Leste', 720, 0.39, 7),
        ('Sul', 6485, 0.03, 11.5),
        ('Oeste', 991, 0.36, 8.5),
        ('Centro', 991, 0.36, 8.5)
    ]
    cursor.executemany("INSERT INTO censo_2010 VALUES (?, ?, ?, ?)", dados_censo_2010)

    # ---------------------------------------------------------
    # TABELA 9: FAIXA ETÁRIA
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE dengue_faixa_etaria (
        ano INTEGER, casos_menor_um_ano INTEGER, casos_1_a_4_anos INTEGER, 
        casos_5_a_9_anos INTEGER, casos_10_a_14_anos INTEGER, casos_15_a_19_anos INTEGER, 
        casos_20_a_39_anos INTEGER, casos_40_a_59_anos INTEGER, casos_60_a_64_anos INTEGER, 
        casos_65_a_69_anos INTEGER, casos_70_a_79_anos INTEGER, casos_maior_80_anos INTEGER
    )""")
    dados_dengue_faixa_etaria = [
        (2020, 120, 671, 1180, 1354, 1480, 6813, 4579, 735, 521, 547, 200),
        (2021, 1, 9, 19, 27, 33, 177, 151, 31, 13, 15, 5),
        (2022, 65, 307, 572, 582, 638, 3181, 2028, 328, 225, 259, 93),
        (2023, 78, 392, 1066, 1155, 1005, 4752, 3248, 515, 428, 484, 181),
        (2024, 310, 1417, 3226, 3541, 3721, 16955, 11474, 1897, 1497, 1732, 761)
    ]
    cursor.executemany("INSERT INTO dengue_faixa_etaria VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", dados_dengue_faixa_etaria)

    print(f"Banco de dados '{DB_FILE}' criado e atualizado com sucesso!")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    criar_e_popular_banco()