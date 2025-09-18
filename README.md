## 🚀 Como Executar o Projeto (Windows)

### Pré-requisitos

Antes de começar, certifique-se de que você tem o seguinte instalado:
[Python 3.8+](https://www.python.org/downloads/)
[Git](https://git-scm.com/downloads/)

**Abra o Terminal do VSCode e execute os comandos abaixo, um por um.**

### Passo 1: Clone o Projeto e Entre na Pasta

Use o Git para baixar o projeto e o comando `cd` para entrar na pasta.

git clone https://github.com/seu-usuario/dashboard-ribeirao-em-dados.git

cd dashboard-ribeirao-em-dados

### Passo 2: Crie e Ative o Ambiente Virtual

Isso cria um ambiente Python isolado para o projeto.

python -m venv .venv

.venv\Scripts\activate

Após ativar, você verá `(.venv)` no início da linha do seu terminal.

### Passo 3: Instale as Bibliotecas

Com o ambiente ativado, instale tudo que o projeto precisa.

pip install -r requirements.txt

### Passo 4: Crie o Banco de Dados

Este comando executa o script que prepara os dados.

python db_local.py

Uma pasta `data/` com o arquivo `db_local.db` será criada.

### Passo 5: Rode o Dashboard

Finalmente, execute o aplicativo Streamlit.

streamlit run app.py

Seu navegador abrirá automaticamente com o dashboard funcionando.