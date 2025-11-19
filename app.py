import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------------
# CONFIGURAÇÃO INICIAL
# ----------------------------------
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ----------------------------------
# CONFIGURANDO GEMINI
# ----------------------------------
api_key = os.getenv("GEMINI_API_KEY")

if api_key and api_key.startswith("AIza"):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    print("✅ Gemini configurado com sucesso.")
else:
    print("⚠️ ERRO: Nenhuma chave válida encontrada no .env")
    model = None

# ----------------------------------
# FUNÇÃO PARA GERAR GRÁFICOS
# ----------------------------------
def gerar_graficos(df):
    graficos = []

    # Gráfico 1 — Vendas por Produto
    if "Produto" in df.columns and "Vendas" in df.columns:
        plt.figure(figsize=(6, 4))
        df.groupby("Produto")["Vendas"].sum().plot(kind="bar")
        plt.title("Vendas por Produto")
        plt.tight_layout()
        path = os.path.join(app.config["UPLOAD_FOLDER"], "grafico_produto.png")
        plt.savefig(path)
        graficos.append(path)

    # Gráfico 2 — Vendas por Mês
    if "Data" in df.columns and "Vendas" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Mês"] = df["Data"].dt.strftime("%Y-%m")
        plt.figure(figsize=(6, 4))
        df.groupby("Mês")["Vendas"].sum().plot(kind="line", marker="o")
        plt.title("Vendas Mensais")
        plt.tight_layout()
        path = os.path.join(app.config["UPLOAD_FOLDER"], "grafico_mes.png")
        plt.savefig(path)
        graficos.append(path)

    return graficos

# ----------------------------------
# ROTA PRINCIPAL
# ----------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------------
# ROTA DE ANÁLISE (CHAT + CSV)
# ----------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        message = request.form.get("message", "").strip()
        uploaded_file = request.files.get("file")

        df = None

        # Se tiver arquivo, carregar CSV/Excel
        if uploaded_file and uploaded_file.filename != "":
            if uploaded_file.filename.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            else:
                return jsonify({"error": "Formato inválido. Envie CSV ou Excel."})

        # Processar dados para o prompt
        dados_texto = df.head(20).to_string() if df is not None else "Nenhuma base enviada."

        # Construir prompt profissional
        prompt = f"""
Você é um analista sênior da Alpha Insights especializado em BI e Vendas.

Sua tarefa:
- Entender os dados enviados
- Responder à pergunta do usuário de forma:
  • Profissional
  • Estruturada
  • Clara
  • Baseada em dados

Primeiras linhas dos dados:
{dados_texto}

Pergunta do usuário:
{message}

Escreva a resposta no formato de um mini-relatório executivo.
"""

        # Se Gemini não configurado
        if not model:
            return jsonify({"response": "Erro: Gemini não configurado no servidor."})

        # Chamada ao modelo
        resposta = model.generate_content(prompt).text

        # Gerar gráficos se houver planilha
        graficos = gerar_graficos(df) if df is not None else []

        return jsonify({
            "response": resposta,
            "graphs": [g.replace("static/", "") for g in graficos]
        })

    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"})

# ----------------------------------
# EXECUÇÃO LOCAL
# ----------------------------------
if __name__ == "__main__":
    app.run(debug=True)
