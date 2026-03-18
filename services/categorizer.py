from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def categorize_transaction(text):

    prompt = f"""
Você é um assistente financeiro.

Extraia da frase do usuário:

- type ("income" ou "expense")
- amount (número)
- category (categoria em português)

Categorias possíveis:

alimentação
transporte
moradia
lazer
saúde
educação
assinaturas
compras
automóvel
salário
outros

Regras:

sushi, pizza, restaurante → alimentação
uber, gasolina, taxi → transporte
remédio, farmácia → saúde
netflix, spotify → assinaturas
salário, pagamento → salário

Responda APENAS com JSON válido neste formato:

{{
"type": "income ou expense",
"amount": 10,
"category": "alimentação"
}}

Frase do usuário:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Responda apenas JSON."},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content

    content = re.sub(r"```json|```", "", content).strip()

    return json.loads(content)