import sqlite3
import os

DB_FILE = "db_local.db"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, DB_FILE)

def criar_e_popular_banco():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela 1: Território (NOVO)
    cursor.execute("CREATE TABLE territorio (id INTEGER PRIMARY KEY, indicador TEXT, valor REAL, unidade TEXT)")
    dados_territorio = [
        ('Área da unidade territorial', 650.955, 'km²'),
        ('Densidade demográfica', 1073.32, 'hab/km²')
    ]
    cursor.executemany("INSERT INTO territorio (indicador, valor, unidade) VALUES (?, ?, ?)", dados_territorio)
    print("Tabela 'territorio' criada com sucesso.")

    # Tabela 2: Demografia (Mantida)
    cursor.execute("CREATE TABLE demografia (id INTEGER PRIMARY KEY, raca TEXT, sexo TEXT, populacao INTEGER)")
    dados_demografia = [
        ('Branca', 'Masculino', 206458), ('Branca', 'Feminino', 238150), ('Preta', 'Masculino', 28034), 
        ('Preta', 'Feminino', 28167), ('Parda', 'Masculino', 94952), ('Parda', 'Feminino', 96741),
        ('Amarela', 'Masculino', 2581), ('Amarela', 'Feminino', 2917), ('Indígena', 'Masculino', 269), ('Indígena', 'Feminino', 325)
    ]
    cursor.executemany("INSERT INTO demografia (raca, sexo, populacao) VALUES (?, ?, ?)", dados_demografia)
    print("Tabela 'demografia' criada com sucesso.")

    # Tabela 3: Saneamento (ATUALIZADA E COMPLETA)
    cursor.execute("CREATE TABLE saneamento (id INTEGER PRIMARY KEY, servico TEXT, tipo TEXT, domicilios INTEGER)")
    dados_saneamento = [
        ('Esgotamento', 'Rede geral, pluvial ou fossa ligada à rede', 261309),
        ('Esgotamento', 'Fossa séptica ou fossa filtro não ligada à rede', 2013),
        ('Esgotamento', 'Fossa rudimentar ou buraco', 2042),
        ('Esgotamento', 'Vala', 74),
        ('Esgotamento', 'Rio, lago, córrego ou mar', 336),
        ('Esgotamento', 'Outra forma', 130),
        ('Lixo', 'Coletado', 265445),
        ('Lixo', 'Queimado na propriedade', 192),
        ('Lixo', 'Enterrado na propriedade', 15),
        ('Lixo', 'Jogado em terreno baldio, encosta ou área pública', 118),
        ('Lixo', 'Outro destino', 165),
        ('Banheiros', 'Sim, um banheiro', 166839),
        ('Banheiros', 'Sim, dois banheiros', 86712),
        ('Banheiros', 'Sim, três ou mais banheiros', 11236),
        ('Banheiros', 'Não', 543)
    ]
    cursor.executemany("INSERT INTO saneamento (servico, tipo, domicilios) VALUES (?, ?, ?)", dados_saneamento)
    print("Tabela 'saneamento' (completa) criada com sucesso.")

    # Tabela 4: Pobreza e Desigualdade (ATUALIZADA E COMPLETA)
    cursor.execute("CREATE TABLE pobreza_desigualdade (id INTEGER PRIMARY KEY, indicador TEXT UNIQUE, media REAL, limite_inferior REAL, limite_superior REAL)")
    dados_pobreza = [
        ('Incidência da pobreza', 11.75, 8.16, 15.35),
        ('Incidência da pobreza subjetiva', 8.77, 7.82, 9.72),
        ('Índice de Gini', 0.45, 0.43, 0.47)
    ]
    cursor.executemany("INSERT INTO pobreza_desigualdade (indicador, media, limite_inferior, limite_superior) VALUES (?, ?, ?, ?)", dados_pobreza)
    print("Tabela 'pobreza_desigualdade' (completa) criada com sucesso.")

    # Tabela 5: Causas de Mortalidade (ATUALIZADA 2017-2022)
    cursor.execute("CREATE TABLE mortalidade_causas (id INTEGER PRIMARY KEY, ano INTEGER, causa TEXT, obitos INTEGER)")
    dados_mortalidade_causas = [
        (2017, 'Neoplasias (tumores)', 906), (2018, 'Neoplasias (tumores)', 913), (2019, 'Neoplasias (tumores)', 911), (2020, 'Neoplasias (tumores)', 900), (2021, 'Neoplasias (tumores)', 900), (2022, 'Neoplasias (tumores)', 956),
        (2017, 'Doenças endócrinas nutricionais e metabólicas', 363), (2018, 'Doenças endócrinas nutricionais e metabólicas', 363), (2019, 'Doenças endócrinas nutricionais e metabólicas', 393), (2020, 'Doenças endócrinas nutricionais e metabólicas', 352), (2021, 'Doenças endócrinas nutricionais e metabólicas', 261), (2022, 'Doenças endócrinas nutricionais e metabólicas', 428),
        (2017, 'Doenças do aparelho circulatório', 1285), (2018, 'Doenças do aparelho circulatório', 1285), (2019, 'Doenças do aparelho circulatório', 1171), (2020, 'Doenças do aparelho circulatório', 1258), (2021, 'Doenças do aparelho circulatório', 1270), (2022, 'Doenças do aparelho circulatório', 1457),
        (2017, 'Doenças do aparelho respiratório', 679), (2018, 'Doenças do aparelho respiratório', 423), (2019, 'Doenças do aparelho respiratório', 759), (2020, 'Doenças do aparelho respiratório', 266), (2021, 'Doenças do aparelho respiratório', 229), (2022, 'Doenças do aparelho respiratório', 324),
        (2017, 'Doenças do aparelho digestivo', 261), (2018, 'Doenças do aparelho digestivo', 299), (2019, 'Doenças do aparelho digestivo', 272), (2020, 'Doenças do aparelho digestivo', 272), (2021, 'Doenças do aparelho digestivo', 283), (2022, 'Doenças do aparelho digestivo', 314),
        (2017, 'Causas externas de morbidade e de mortalidade', 452), (2018, 'Causas externas de morbidade e de mortalidade', 477), (2019, 'Causas externas de morbidade e de mortalidade', 421), (2020, 'Causas externas de morbidade e de mortalidade', 473), (2021, 'Causas externas de morbidade e de mortalidade', 473), (2022, 'Causas externas de morbidade e de mortalidade', 523)
    ]
    cursor.executemany("INSERT INTO mortalidade_causas (ano, causa, obitos) VALUES (?, ?, ?)", dados_mortalidade_causas)
    print("Tabela 'mortalidade_causas' (expandida) criada com sucesso.")

    conn.commit()
    conn.close()
    
    print(f"\nSUCESSO! O banco de dados '{DB_FILE}' foi ATUALIZADO na pasta '{DATA_DIR}/'.")

if __name__ == '__main__':
    criar_e_popular_banco()