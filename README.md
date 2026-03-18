# 💰 Finance AI Agent (Telegram Bot)

Agente financeiro inteligente via Telegram que interpreta linguagem natural, categoriza transações automaticamente com IA e gera relatórios completos em HTML e PDF.

---

## 🚀 Visão Geral

Este projeto é um assistente financeiro pessoal automatizado, capaz de:

* Interpretar mensagens como: *"gastei 50 no mercado"*
* Classificar receitas e despesas automaticamente com IA
* Armazenar dados estruturados em banco PostgreSQL (Render)
* Gerar dashboards e relatórios financeiros
* Produzir arquivos HTML e PDF prontos para envio

---

## 🧠 Diferencial (IA aplicada)

Uso de LLM (OpenAI) para:

* Extração de dados de linguagem natural
* Classificação automática (income / expense)
* Normalização de categorias
* Fallback inteligente quando regex falha

---

## 🏗️ Arquitetura do Projeto

```
project/
│
├── bot/
│   ├── __init__.py
│   └── main.py              # Entry point do bot (Telegram)
│
├── services/
│   └── categorizer.py       # IA: parsing de texto → JSON
│
├── database/
│   ├── __init__.py
│   ├── models.py            # ORM (SQLAlchemy)
│   └── crud.py              # Operações no banco
│
├── reports/
│   ├── __init__.py
│   └── report_generator.py  # Geração de relatórios
│
├── alembic/                 # Controle de migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── wait-for-it.sh
```

---

## ⚙️ Tecnologias Utilizadas

* Python 3.11
* Telegram Bot API (`python-telegram-bot`)
* OpenAI API (GPT-4o-mini)
* SQLAlchemy
* Alembic (migrations)
* PostgreSQL (Render)
* Matplotlib
* PDFKit + wkhtmltopdf
* Docker
* AWS (EC2)

---

## ☁️ Deploy e Infraestrutura

O projeto está em produção utilizando uma arquitetura híbrida:

### 🖥️ Aplicação (AWS)

* Deploy realizado em instância EC2 (Ubuntu)
* Containerização com Docker
* Execução contínua com política:

```bash
docker run -d \
  --name finance_bot \
  --restart always \
  --env-file .env \
  finance-agent
```

### 🗄️ Banco de Dados (Render)

* PostgreSQL gerenciado
* Conexão via variável de ambiente `DATABASE_URL`
* Persistência segura e independente da aplicação

### ✅ Resultado

* Bot rodando 24/7 na nuvem
* Totalmente desacoplado da máquina local
* Alta disponibilidade
* Arquitetura próxima de produção real

---

## 📊 Funcionalidades

### 💬 Entrada em linguagem natural

"Gastei 120 no mercado"
"Recebi 3000 de salário"
"Paguei 45 de Uber"

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

5. Dados salvos no PostgreSQL
6. Dashboard atualizado

---

## 🧬 Banco de Dados e Migrations

O projeto utiliza Alembic para versionamento do banco.

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
DATABASE_URL=your_render_postgres_url
```

---

## 📌 Decisões Técnicas

✔️ **LLM para parsing**
Permite entrada flexível e natural.

✔️ **PostgreSQL (Render)**
Banco robusto e pronto para produção.

✔️ **Alembic**
Controle profissional de versionamento de banco.

✔️ **Base64 nos relatórios**
Resolve problema de envio via Telegram (arquivo único).

✔️ **Docker + AWS**
Deploy escalável e independente de ambiente local.

✔️ **Arquitetura em camadas**

* `services` → lógica de negócio (IA)
* `database` → persistência
* `reports` → geração de saída

---

## 🚧 Próximos Passos

* CI/CD (deploy automático)
* Monitoramento (logs e alertas)
* Dashboard web (React)
* Multi-usuário real
* Cache de respostas da IA
* Integração com Open Finance

---

## 👨‍💻 Autor

José Faria Neto

* Data Analytics (FIAP)
* Foco em IA aplicada e engenharia de software

---

## 💡 Sobre o Projeto

Projeto desenvolvido para demonstrar:

* Integração real com IA (LLM)
* Arquitetura backend moderna
* Deploy em nuvem (AWS + Render)
* Automação financeira
* Geração de relatórios inteligentes

---

## ⭐ Destaque para Recrutadores

Este projeto demonstra:

* Uso prático de IA em produto real
* Deploy em cloud (AWS EC2 + PostgreSQL gerenciado)
* Arquitetura escalável
* Integração com APIs externas
* Boas práticas de engenharia de software
* Pensamento de produto + engenharia
