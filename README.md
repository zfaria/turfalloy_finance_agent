# 💰 Finance AI Agent (Telegram Bot)

Agente financeiro inteligente via Telegram que interpreta linguagem natural, categoriza transações automaticamente com IA e gera relatórios completos em HTML e PDF.

---

## 🚀 Visão Geral

Este projeto é um **assistente financeiro pessoal automatizado**, capaz de:

* Interpretar mensagens como: *"gastei 50 no mercado"*
* Classificar receitas e despesas automaticamente com IA
* Armazenar dados estruturados em banco SQLite
* Gerar dashboards e relatórios financeiros
* Produzir arquivos HTML e PDF prontos para envio

---

## 🧠 Diferencial (IA aplicada)

Uso de LLM (OpenAI) para:

* Extração de dados de linguagem natural
* Classificação automática (`income` / `expense`)
* Normalização de categorias
* Fallback inteligente quando regex falha

---

## 🏗️ Arquitetura do Projeto

```id="arch1"
project/
│
├── main.py                  # Entry point do bot (Telegram)
│
├── services/
│   └── categorizer.py       # IA: parsing de texto → JSON estruturado
│
├── database/
│   ├── models.py            # ORM (SQLAlchemy)
│   └── crud.py              # Operações no banco
│
├── reports/
│   ├── report_generator.py  # Geração de relatórios
│   ├── dashboard_template.html
│   └── *.html / *.pdf / *.png
│
├── alembic/                 # Controle de migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── alembic.ini
├── finance.db
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── wait-for-it.sh
```

---

## ⚙️ Tecnologias Utilizadas

* Python 3.11
* Telegram Bot API (`python-telegram-bot`)
* OpenAI API (GPT-4o-mini)
* SQLAlchemy
* Alembic (migrations)
* SQLite
* Matplotlib
* PDFKit + wkhtmltopdf
* Docker

---

## 📊 Funcionalidades

### 💬 Entrada em linguagem natural

```
"Gastei 120 no mercado"
"Recebi 3000 de salário"
"Paguei 45 de Uber"
```

---

### 📈 Dashboard

* Receita total
* Despesas
* Saldo
* Maior categoria de gasto

---

### 📉 Gráficos

* Distribuição de gastos por categoria
* Evolução do saldo acumulado ao longo do tempo

---

### 🧠 Análise automática

* Situação financeira (positiva/negativa)
* Categoria com maior gasto
* Insights simples de comportamento

---

### 📄 Relatórios

* HTML completo
* PDF para download
* Gráficos embutidos (Base64)
* Envio direto via Telegram

---

## 🔄 Fluxo do Sistema

1. Usuário envia mensagem no Telegram
2. Sistema tenta parsing via regex
3. Fallback para IA (OpenAI)
4. Estrutura gerada:

```json
{
  "type": "expense",
  "amount": 50,
  "category": "alimentacao"
}
```

5. Dados salvos no banco
6. Dashboard atualizado

---

## 🧬 Banco de Dados e Migrations

O projeto utiliza **Alembic** para versionamento do banco.

### Criar migration

```bash
alembic revision --autogenerate -m "nova tabela"
```

### Aplicar migrations

```bash
alembic upgrade head
```

---

## 🐳 Rodando com Docker

```bash
docker build -t finance-agent .
docker run -d --env-file .env finance-agent
```

---

## 🔐 Variáveis de Ambiente

```
TELEGRAM_TOKEN=your_token
OPENAI_API_KEY=your_key
```

---

## 📌 Decisões Técnicas

### ✔️ LLM para parsing

Permite entrada flexível e natural.

---

### ✔️ Alembic

Controle profissional de versionamento de banco (padrão de mercado).

---

### ✔️ Base64 nos relatórios

Resolve problema de envio via Telegram (arquivo único).

---

### ✔️ SQLite

Ideal para MVP e portabilidade.

---

### ✔️ Arquitetura em camadas

* `services` → lógica de negócio (IA)
* `database` → persistência
* `reports` → geração de saída

---

## 🚧 Próximos Passos

* Deploy (AWS / Render)
* Dashboard web (React)
* Multi-usuário real
* Cache de respostas IA
* Integração com Open Finance

---

## 👨‍💻 Autor

**José Faria Neto**

* Data Analytics (FIAP)
* Foco em IA aplicada e engenharia de software

---

## 💡 Sobre o Projeto

Projeto desenvolvido para demonstrar:

* Integração real com IA (LLM)
* Arquitetura backend moderna
* Automação financeira
* Geração de relatórios inteligentes

---

## ⭐ Destaque para Recrutadores

Este projeto demonstra:

* Uso prático de IA em produto real
* Controle de migrations com Alembic
* Integração com APIs externas
* Arquitetura escalável
* Pensamento de produto + engenharia

---
