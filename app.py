from flask import Flask, render_template, request, jsonify
from google import genai
import pandas as pd
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        message = request.form.get("message")
        file = request.files.get("file")

        if not message:
            return jsonify({"error": "Mensagem vazia"}), 400

        csv_content = ""
        if file:
            df = pd.read_csv(file)
            csv_content = df.to_csv(index=False)

        prompt = f"""
Você é um analista profissional altamente qualificado.

REGRAS:
- Sua resposta deve ser objetiva, porém robusta.
- Use subtítulos, bullet points e estrutura profissional.
- Destaque insights, riscos, ações recomendadas e análises relevantes.
- Seja preciso, claro e extremamente organizado.

Mensagem do usuário:
{message}

Dados enviados (CSV):
{csv_content if file else "Nenhum arquivo enviado"}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
