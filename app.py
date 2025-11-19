import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import google.generativeai as genai

# ------------------------------
# Configurações Iniciais
# ------------------------------
load_dotenv()
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    print("⚠️ Chave Gemini não encontrada")

# ------------------------------
# Geração de gráficos
# ------------------------------
def gerar_graficos(df):
    graficos = []

    # Vendas por Produto
    if 'Produto' in df.columns and 'Vendas' in df.columns:
        plt.figure(figsize=(6, 4))
        df.groupby('Produto')['Vendas'].sum().plot(kind='bar', color='teal')
        plt.title('Vendas por Produto')
        plt.ylabel('Total de Vendas')
        path = os.path.join(app.config['UPLOAD_FOLDER'], 'grafico_produto.png')
        plt.tight_layout()
        plt.savefig(path)
        graficos.append(path)

    # Vendas por Mês
    if 'Data' in df.columns and 'Vendas' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Mês'] = df['Data'].dt.strftime('%Y-%m')
        plt.figure(figsize=(6, 4))
        df.groupby('Mês')['Vendas'].sum().plot(kind='line', marker='o', color='orange')
        plt.title('Vendas por Mês')
        plt.ylabel('Total de Vendas')
        path = os.path.join(app.config['UPLOAD_FOLDER'], 'grafico_mes.png')
        plt.tight_layout()
        plt.savefig(path)
        graficos.append(path)

    return graficos

# ------------------------------
# Página inicial
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------------------
# Rota do Chat + CSV
# ------------------------------
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        message = request.form.get("message", "")

        df = None
        if "file" in request.files:
            file = request.files["file"]

            if file.filename.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            elif file.filename != "":
                return jsonify({"error": "Formato não suportado (use CSV ou Excel)"})

        # Se não houver modelo
        if not model:
            return jsonify({"response": "Erro: Gemini não configurado no servidor."})

        # Criar contexto de dados
        dados_str = df.head(20).to_string() if df is not None else "Nenhum arquivo enviado."

        prompt = f"""
Você é um assistente sênior da Alpha Insights especializado em análise de vendas e BI.

Sua tarefa:

1. Interpretar os dados enviados (CSV/Excel)
2. Analisar a pergunta do usuário
3. Responder com:
   • Estrutura profissional  
   • Clareza  
   • Dados relevantes  
   • Tom consultivo  
   • Orientação prática

Dados (primeiras 20 linhas):
{dados_str}

Pergunta: {message}

Escreva uma resposta robusta, objetiva e profissional, como em um relatório executivo curto.
"""

        response = model.generate_content(prompt)
        resposta = response.text

        return jsonify({"response": resposta})

    except Exception as e:
        return jsonify({"error": str(e)})

# ------------------------------
# Execução local
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
