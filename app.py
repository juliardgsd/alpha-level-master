import os
from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import google.generativeai as genai

# ------------------------------
# Configurações Iniciais
# ------------------------------
load_dotenv()
app = Flask(__name__)

# Configuração do app
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# ------------------------------
# Configuração do Gemini
# ------------------------------
api_key = os.getenv('GEMINI_API_KEY')
if api_key and api_key.startswith("AIza"):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    print("✅ Gemini configurado com sucesso.")
else:
    model = None
    print("⚠️ Nenhuma chave Gemini encontrada no .env")


# ------------------------------
# Função para gerar gráficos
# ------------------------------
def gerar_graficos(df):
    """Gera gráficos básicos e retorna os caminhos dos arquivos."""
    graficos = []

    # Gráfico de vendas por produto
    if 'Produto' in df.columns and 'Vendas' in df.columns:
        plt.figure(figsize=(6, 4))
        df.groupby('Produto')['Vendas'].sum().plot(kind='bar', color='teal')
        plt.title('Vendas por Produto')
        plt.ylabel('Total de Vendas')
        plt.tight_layout()
        caminho1 = os.path.join(app.config['UPLOAD_FOLDER'], 'grafico_vendas_produto.png')
        plt.savefig(caminho1)
        graficos.append(caminho1)

    # Gráfico de vendas por mês
    if 'Data' in df.columns and 'Vendas' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Mês'] = df['Data'].dt.strftime('%Y-%m')
        plt.figure(figsize=(6, 4))
        df.groupby('Mês')['Vendas'].sum().plot(kind='line', marker='o', color='orange')
        plt.title('Vendas Mensais')
        plt.ylabel('Total de Vendas')
        plt.tight_layout()
        caminho2 = os.path.join(app.config['UPLOAD_FOLDER'], 'grafico_vendas_mes.png')
        plt.savefig(caminho2)
        graficos.append(caminho2)

    return graficos


# ------------------------------
# Rotas
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return render_template('index.html', error="Nenhum arquivo enviado.")

    file = request.files['file']
    pergunta = request.form.get('question', '')

    if file.filename == '':
        return render_template('index.html', error="Nenhum arquivo selecionado.")

    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(caminho_arquivo)

    # ------------------------------
    # Suporte a CSV e Excel
    # ------------------------------
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(caminho_arquivo)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(caminho_arquivo)
        else:
            return render_template('index.html', error="Formato de arquivo não suportado. Envie CSV ou Excel.")
    except Exception as e:
        return render_template('index.html', error=f"Erro ao ler o arquivo: {e}")

    graficos = gerar_graficos(df)

    resposta = "Não foi possível gerar análise no momento."
    if model:
        try:
            prompt = f"""
            Você é um analista de vendas da Alpha Insights.
            Analise a planilha de vendas a seguir e responda à pergunta do usuário.

            Dados:
            {df.head(20).to_string()}

            Pergunta: {pergunta}

            Gere uma resposta profissional e objetiva.
            """
            response = model.generate_content(prompt)
            resposta = response.text
        except Exception as e:
            resposta = f"Erro ao gerar resposta com Gemini: {e}"

    return render_template('index.html', answer=resposta, graphs=graficos)


# ------------------------------
# Execução
# ------------------------------
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
