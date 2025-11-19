from flask import Flask, render_template, request
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração da API Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analisar", methods=["POST"])
def analisar():
    try:
        usuario_prompt = request.form.get("prompt")
        arquivo = request.files.get("arquivo")

        if not usuario_prompt:
            return "Erro: O campo de prompt está vazio."

        df = None
        if arquivo:
            try:
                df = pd.read_csv(arquivo)
            except Exception:
                return "Erro ao ler o arquivo CSV. Verifique o formato."

        # Construção do prompt final
        prompt_final = f"""
Você é um modelo de IA que deve responder de forma objetiva, clara e profissional.

Prompt do usuário:
{usuario_prompt}

Dados enviados (CSV):
{df.to_string() if df is not None else "Nenhum arquivo CSV enviado."}

Gere uma resposta organizada, profissional e direta.
"""

        resposta = model.generate_content(prompt_final)
        return resposta.text

    except Exception as e:
        return f"Ocorreu um erro: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
