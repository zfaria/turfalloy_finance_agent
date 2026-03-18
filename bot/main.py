import os
import json
import logging
import random
import re
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import OpenAI

from database.models import init_db
from database.crud import (
    add_transaction,
    get_month_summary,
    get_last_transactions,
    get_dashboard_data,
    get_expenses_by_category,
    get_monthly_analysis,
)

import matplotlib.pyplot as plt
from reports.report_generator import generate_html_report
from services.categorizer import categorize_transaction
import traceback

# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ==============================
# CONFIGURAÇÕES
# ==============================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# ==============================
# MENU
# ==============================

MENU_OPTIONS = {
    "📊 Dashboard": "dashboard",
    "📈 Resumo": "resumo", 
    "🧾 Extrato": "extrato",
    "📉 Gráfico": "grafico",
    "❓ Ajuda": "ajuda",
    "🧠 Análise": "analise",
    "📊 Relatório": "relatorio"
}

menu = ReplyKeyboardMarkup(
    [
        ["📊 Dashboard", "📈 Resumo"],
        ["🧾 Extrato", "📉 Gráfico"],
        ["❓ Ajuda", "🧠 Análise"],
        ["📊 Relatório"],
    ],
    resize_keyboard=True,
)


# ==============================
# UTILITÁRIOS
# ==============================

def format_currency(value):
    """Formata valor no padrão brasileiro: 2.500,00"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_greeting():
    """Retorna saudação baseada no horário."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return random.choice(["Bom dia", "Olá", "Oi"])
    elif 12 <= hour < 18:
        return random.choice(["Boa tarde", "Olá", "Oi"])
    else:
        return random.choice(["Boa noite", "Olá", "Oi"])


# ==============================
# RESPOSTAS NATURAIS
# ==============================

# Padrões de linguagem natural para detecção - EXPANDIDOS
PATTERNS = {
    'greeting': r'\b(oi|olá|ola|eae|e aí|opa|fala|bom dia|boa tarde|boa noite|salve|hey|hi|hello)\b',
    
    'help_request': r'\b(ajuda|help|como (funciona|usa|usar|faço|fazer|posso|consigo)|o que (faz|fazer|você faz)|quem é você|'
                   r'não (sei|entendi|funciona)|não (sei|consigo) (usar|fazer)|'
                   r'como (eu )?(isso|esse|isso funciona)|'
                   r'(me )?ajud[ae]|explica|tutorial|instruções|'
                   r'onde (está|fica|encontro)|como (acesso|vejo|acho)|'
                   r'pra que (serve|isso)|qual (a|é a) (função|utilidade)|'
                   r'pode (me )?ajudar|me ajuda|ajuda (eu|por favor)|'
                   r'(estou|to) perdido|não (sei|entendo) (nada|o que fazer)|'
                   r'primeira vez|começar|iniciar)\b',
    
    'gratitude': r'\b(obrigad[oa]|valeu|vlw|thanks|thank you|grato|agradeço|muito obrigado|'
                 r'obrigado pela ajuda|obrigada|valeu mesmo|obg|obrig)\b',
    
    'goodbye': r'\b(tchau|até|até mais|até logo|flw|falou|xau|bye|goodbye|see you|'
               r'até amanhã|até depois|fui|vou nessa)\b',
    
    'status_check': r'\b(como (estou|tô|andam|vai|vão)|resumo|situação|status|'
                    r'quanto (gastei|tenho|sobrou|falta)|meu saldo|'
                    r'finanças|extrato|movimentação|conta|balanço)\b',
    
    'wellbeing': r'\b(como (vai|vai você|você está|vc ta)|tudo bem|tudo bom|tudo certo|'
                 r'beleza|tranquilo|e você|e ai|e aí|como (está|ta))\b',
    
    'confirmation': r'\b(sim|yes|claro|pode|ok|beleza|show|legal|perfeito|ótimo|'
                   r'vamos lá|vamo|bora|pode ser|tudo bem|combinado)\b',
    
    'denial': r'\b(não|nao|no|nope|não quero|deixa|cancela|esquece|não obrigado|'
              r'agora não|depois|outra hora)\b'
}

NATURAL_RESPONSES = {
    'greeting': [
        "{greeting}! 👋 Pronto pra organizar suas finanças? Me conta o que você ganhou ou gastou!",
        "{greeting}! 💰 Que tal registrar uma transação? Ou use os botões abaixo!",
        "{greeting}! 🚀 Vamos cuidar do seu dinheiro? Me diz o que aconteceu!",
        "{greeting}! 😊 Posso ajudar com receitas, despesas ou mostrar seus relatórios!",
    ],
    
    'help_request': [
        "Claro! 💡 Posso registrar suas receitas e despesas automaticamente.\n\n"
        "📝 <b>Como usar:</b>\n"
        "• Escreva: <i>'Gastei 50 no mercado'</i>\n"
        "• Ou: <i>'Ganhei 3000 de salário'</i>\n"
        "• Ou use os botões abaixo para ver gráficos e relatórios!\n\n"
        "O que você quer fazer? 👇",
        
        "Posso te ajudar sim! 🎯\n\n"
        "Eu sou seu assistente financeiro. Você pode:\n"
        "• Registrar gastos: <i>'Paguei 30 de Uber'</i>\n"
        "• Registrar ganhos: <i>'Recebi 500 de freelance'</i>\n"
        "• Ver seu dashboard, gráficos e análises nos botões abaixo!\n\n"
        "Tenta aí! 😊",
        
        "Oi! Deixa eu explicar... 🤝\n\n"
        "É simples: me conta o que você gastou ou recebeu em linguagem natural. "
        "Exemplos:\n"
        "• <i>'Gastei 150 no mercado hoje'</i>\n"
        "• <i>'Meu salário de 4000 caiu'</i>\n\n"
        "Ou explore os botões para ver seus dados! 📊",
    ],
    
    'gratitude': [
        "Por nada! 😊 Fico feliz em ajudar com suas finanças!",
        "Disponha! 💪 Conte comigo sempre que precisar!",
        "De nada! 🎯 Que tal registrar mais uma transação agora?",
        "Imagina! 🙌 Estou aqui pra isso!",
    ],
    
    'goodbye': [
        "Até mais! 💰 Volte sempre que precisar organizar suas finanças!",
        "Tchau! 🚀 Lembre-se: registrar pequenos gastos faz grande diferença!",
        "Falou! 📊 Estarei aqui quando precisar!",
        "Até logo! 👋 Cuide bem do seu dinheiro!",
    ],
    
    'wellbeing': [
        "Vou bem, obrigado! 😄 E você, como estão suas finanças hoje?",
        "Tudo certo por aqui! 💚 Pronto pra ajudar você a economizar!",
        "Ótimo! 🎯 E aí, registrou alguma movimentação hoje?",
        "Bem, bem! 😊 E suas finanças, como andam?",
    ],
    
    'confirmation': [
        "Perfeito! 🎉 Pode começar quando quiser!",
        "Show! 👍 Estou pronto pra ajudar!",
        "Legal! 😊 Me conta sua primeira transação!",
    ],
    
    'denial': [
        "Tudo bem! 😊 Quando quiser, é só chamar!",
        "Sem problema! 👍 Estou aqui quando precisar!",
        "Ok! 📝 Só me avisar se mudar de ideia!",
    ],
    
    'not_understood': [
        "Hmm, não entendi muito bem... 🤔\n\n"
        "Posso registrar transações como <i>'Gastei 50 no mercado'</i> ou mostrar seus dados. "
        "O que você gostaria de fazer?\n\n"
        "Se precisar de ajuda, digite <b>'ajuda'</b>!",
        
        "Não captei... 💭\n\n"
        "Quer registrar uma despesa/receita? Ou prefere ver seu dashboard? "
        "Me fala ou use os botões abaixo!\n\n"
        "Posso te ajudar se escrever <b>'como usar'</b>!",
        
        "Deixa eu ver... 🤷‍♂️\n\n"
        "Se quiser registrar algo, escreva tipo <i>'Ganhei 1000 de freelance'</i>. "
        "Ou escolha uma opção no menu!\n\n"
        "Dica: digite <b>'ajuda'</b> pra ver como funciona!",
        
        "Ops, não entendi! 😅\n\n"
        "Tenta escrever assim:\n"
        "• <i>'Gastei 45 de Uber'</i>\n"
        "• <i>'Recebi salário de 3000'</i>\n"
        "• Ou digite <b>'ajuda'</b> pra ver todas as opções!",
    ]
}


def detect_intent(message: str) -> str:
    """Detecta a intenção do usuário baseada em padrões."""
    message_lower = message.lower().strip()
    
    # Remover pontuação excessiva para melhor matching
    message_clean = re.sub(r'[?!.]{2,}', '!', message_lower)
    
    for intent, pattern in PATTERNS.items():
        if re.search(pattern, message_clean):
            return intent
    return 'unknown'


def get_natural_response(intent: str, context_data: dict = None) -> str:
    """Retorna uma resposta natural baseada na intenção."""
    if intent in NATURAL_RESPONSES:
        template = random.choice(NATURAL_RESPONSES[intent])
        if '{greeting}' in template:
            template = template.format(greeting=get_greeting())
        return template
    return None


# ==============================
# FALLBACK GPT - INTELIGÊNCIA NATURAL
# ==============================

def classify_intent_with_gpt(message: str) -> dict:
    """
    Usa GPT para classificar intenção quando regex falha.
    Retorna dict com 'intent' e 'confidence'.
    """
    try:
        system_prompt = """Você é um classificador de intenções para um bot de finanças pessoais.
Analise a mensagem do usuário e determine a intenção principal.

Intenções possíveis:
- greeting: Saudações (oi, olá, bom dia, etc)
- help_request: Pedido de ajuda, tutorial, instruções, "como usar", "não sei usar", "me ajuda"
- gratitude: Agradecimentos (obrigado, valeu, etc)
- goodbye: Despedidas (tchau, até mais, etc)
- wellbeing: Perguntas sobre como o bot está ("tudo bem?", "como vai?")
- status_check: Ver situação financeira ("como estou?", "meu saldo", etc)
- confirmation: Confirmações (sim, ok, claro, etc)
- denial: Negações (não, agora não, etc)
- transaction: Registro de receita/despesa (contém valores, produtos, serviços)
- unknown: Não se encaixa em nenhuma acima

Responda APENAS em JSON no formato: {"intent": "nome_da_intencao", "confidence": 0.0-1.0}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Mensagem: '{message}'"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"GPT intent classification: {result} para mensagem: '{message}'")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao classificar intenção com GPT: {e}")
        return {"intent": "unknown", "confidence": 0.0}


# ==============================
# COMANDOS
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Boas-vindas personalizada."""
    greeting = get_greeting()
    user_name = update.effective_user.first_name or "amigo"
    
    await update.message.reply_text(
        f"{greeting}, {user_name}! 👋\n\n"
        f"Sou seu <b>Agente Financeiro Pessoal</b>. "
        f"Organizo suas finanças de forma simples e inteligente.\n\n"
        f"💬 <b>Como usar:</b>\n"
        f"• <i>Ganhei R$3000 de salário</i>\n"
        f"• <i>Recebi 500 de freelance</i>\n"
        f"• <i>Gastei R$150 no mercado</i>\n"
        f"• <i>Paguei 45 de Uber</i>\n\n"
        f"Ou use os botões abaixo para navegar! 👇",
        reply_markup=menu,
        parse_mode="HTML"
    )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ajuda - Exibe ajuda contextual."""
    text = (
        "❓ <b>Precisa de ajuda?</b>\n\n"
        
        "📝 <b>Registrar Transações:</b>\n"
        "• <i>Ganhei/Recebi/Salário</i> → Receita 💰\n"
        "• <i>Gastei/Paguei/Comprei</i> → Despesa 💸\n\n"
        
        "📊 <b>Botões disponíveis:</b>\n"
        "• 📊 Dashboard → Visão geral\n"
        "• 📈 Resumo → Mês atual\n"
        "• 🧾 Extrato → Últimas transações\n"
        "• 📉 Gráfico → Despesas por categoria\n"
        "• 🧠 Análise → Insights inteligentes\n"
        "• 📊 Relatório → HTML completo\n\n"
        
        "💡 <b>Dica:</b> Quanto mais específico, melhor! "
        "Em vez de 'gastei dinheiro', diga 'gastei 50 reais com Uber'."
    )
    await update.message.reply_text(text, reply_markup=menu, parse_mode="HTML")


async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /resumo - Exibe resumo do mês com tom natural."""
    user_id = str(update.effective_user.id)
    summary = get_month_summary(user_id)
    
    balance = summary['balance']
    
    # Mensagem contextual baseada na situação
    if balance > 1000:
        status_msg = "Excelente! 🎉 Você está com um ótimo saldo!"
    elif balance > 0:
        status_msg = "Bom trabalho! ✅ Você está no positivo."
    elif balance == 0:
        status_msg = "Equilibrado! ⚖️ Receitas = Despesas."
    else:
        status_msg = "Atenção! 🚨 Você está gastando mais do que recebe."
    
    message = (
        f"📊 <b>Resumo do Mês</b>\n\n"
        f"{status_msg}\n\n"
        f"💰 Receitas: R${format_currency(summary['income'])}\n"
        f"💸 Despesas: R${format_currency(summary['expense'])}\n"
        f"📈 Saldo: R${format_currency(balance)}"
    )
    
    if balance < 0:
        message += "\n\n⚠️ <b>Dica:</b> Que tal revisar suas maiores despesas?"
    
    await update.message.reply_text(message, reply_markup=menu, parse_mode="HTML")


async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /extrato - Lista últimas transações."""
    user_id = str(update.effective_user.id)
    transactions = get_last_transactions(user_id, limit=10)

    if not transactions:
        await update.message.reply_text(
            "📝 Ainda não temos transações registradas.\n\n"
            "Que tal começar? Me conta o que você ganhou ou gastou hoje!",
            reply_markup=menu
        )
        return

    text = "🧾 <b>Últimas Movimentações</b>\n\n"
    
    for t in transactions:
        emoji = "🟢" if t.type == "income" else "🔴"
        tipo = "Entrada" if t.type == "income" else "Saída"
        
        text += (
            f"{emoji} <b>{t.created_at.strftime('%d/%m')}</b> | "
            f"{t.category}\n"
            f"   {tipo}: R${format_currency(t.amount)}\n\n"
        )

    await update.message.reply_text(text, reply_markup=menu, parse_mode="HTML")


async def grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /grafico - Gera gráfico de despesas."""
    user_id = str(update.effective_user.id)
    data = get_expenses_by_category(user_id)

    if not data:
        await update.message.reply_text(
            "📊 Ainda não tenho despesas suficientes pra fazer um gráfico legal.\n\n"
            "Registra algumas compras primeiro! 💳",
            reply_markup=menu
        )
        return

    # Ordenar do maior para o menor
    data_sorted = sorted(data, key=lambda x: x[1], reverse=True)
    
    # Top 8 + Outros
    if len(data_sorted) > 8:
        top_8 = data_sorted[:8]
        others_sum = sum([float(d[1]) for d in data_sorted[8:]])
        display_data = sorted(top_8 + [("Outros", others_sum)], key=lambda x: x[1], reverse=True)
    else:
        display_data = data_sorted

    categories = [d[0][:15] + "..." if len(d[0]) > 15 else d[0] for d in display_data]
    values = [float(d[1]) for d in display_data]
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#FFB6C1']

    plt.figure(figsize=(12, 7))
    bars = plt.bar(range(len(categories)), values, 
                   color=colors[:len(categories)], 
                   edgecolor='white', 
                   linewidth=1.5,
                   width=0.7)
    
    plt.xticks(range(len(categories)), categories, rotation=45, ha='right')
    plt.title("Despesas por Categoria", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Valor (R$)", fontsize=12)
    plt.xlabel("Categoria", fontsize=12)
    
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                f'R$ {format_currency(value)}', 
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.ylim(0, max(values) * 1.15)
    plt.tight_layout()
    
    file_path = f"grafico_{user_id}.png"
    plt.savefig(file_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    total = sum([float(d[1]) for d in data_sorted])
    
    # Mensagem contextual
    top_cat = display_data[0][0]
    msg = (
        f"📉 <b>Aqui está seu mapa de gastos!</b>\n\n"
        f"💸 Total: R${format_currency(total)}\n"
        f"🏆 Maior categoria: {top_cat}\n\n"
        f"Quer saber como economizar? Use o botão 🧠 Análise!"
    )
    
    await update.message.reply_photo(
        photo=open(file_path, "rb"),
        caption=msg,
        reply_markup=menu,
        parse_mode="HTML"
    )
    
    try:
        os.remove(file_path)
    except:
        pass


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /dashboard - Visão geral financeira."""
    user_id = str(update.effective_user.id)
    data = get_dashboard_data(user_id)

    income = data.get("income", 0)
    expense = data.get("expense", 0)
    balance = data.get("balance", 0)
    total_transactions = data.get("total_transactions", 0)

    if data.get("top_category"):
        category, category_value = data["top_category"]
        category_text = f"🏆 {category} (R${format_currency(category_value)})"
    else:
        category_text = "🏆 Nenhuma despesa ainda"

    balance_emoji = "🟢" if balance >= 0 else "🔴"
    
    message = (
        "📊 <b>Seu Dashboard Financeiro</b>\n\n"
        f"💰 Receitas: R${format_currency(income)}\n"
        f"💸 Despesas: R${format_currency(expense)}\n"
        f"{balance_emoji} Saldo: R${format_currency(balance)}\n\n"
        f"<b>Maior Gasto:</b> {category_text}\n"
        f"📝 Total de transações: {total_transactions}\n\n"
        f"Continue registrando! Cada centavo conta. 💪"
    )

    await update.message.reply_text(message, reply_markup=menu, parse_mode="HTML")


async def analise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /analise - Análise detalhada com tom consultivo."""
    user_id = str(update.effective_user.id)
    data = get_monthly_analysis(user_id)

    if not data:
        await update.message.reply_text(
            "📝 Preciso de mais dados pra fazer uma análise legal.\n\n"
            "Registra umas despesas primeiro e volte aqui! 😉",
            reply_markup=menu
        )
        return

    total = sum(item[1] for item in data)
    biggest = max(data, key=lambda x: x[1])
    percent = (biggest[1] / total) * 100 if total > 0 else 0
    
    # Análise personalizada
    if percent > 40:
        analysis = (
            f"⚠️ <b>Atenção!</b> Você está gastando muito com <b>{biggest[0]}</b>.\n"
            f"Isso representa {percent:.1f}% do seu total! "
            f"Que tal criar um limite pra essa categoria?"
        )
    elif percent > 25:
        analysis = (
            f"💡 <b>Observação:</b> <b>{biggest[0]}</b> é sua maior despesa ({percent:.1f}%).\n"
            f"Nada alarmante, mas vale a pena monitorar."
        )
    else:
        analysis = (
            f"✅ <b>Parabéns!</b> Seus gastos estão bem distribuídos.\n"
            f"<b>{biggest[0]}</b> é só {percent:.1f}% do total. Continue assim!"
        )

    message = (
        "🧠 <b>Análise Inteligente</b>\n\n"
        f"💸 Total gasto: R${format_currency(total)}\n\n"
        f"📊 <b>{biggest[0]}</b>: R${format_currency(biggest[1])} ({percent:.1f}%)\n\n"
        f"{analysis}"
    )

    await update.message.reply_text(message, reply_markup=menu, parse_mode="HTML")

# ==============================
# RELATORIO COMPLETO - HTML + PDF
# ==============================

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /relatorio - Gera relatório HTML e PDF."""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text(
        "📊 Estou preparando seu relatório completo... "
        "Isso pode levar alguns segundos! ⏱️",
        reply_markup=menu
    )
    
    try:
        # Importar e verificar status
        from reports.report_generator import generate_html_report, PDF_AVAILABLE, PDF_METHOD, PDF_ERROR
        
        logger.info(f"PDF_AVAILABLE: {PDF_AVAILABLE}, PDF_METHOD: {PDF_METHOD}")
        if PDF_ERROR:
            logger.warning(f"PDF_ERROR: {PDF_ERROR}")
        
        # Gerar relatório
        result = generate_html_report(user_id, generate_pdf=True)
        
        logger.info(f"Resultado: HTML={result.get('html')}, PDF={result.get('pdf')}")
        
        # Verificar se HTML existe
        html_path = result.get('html')
        if html_path and os.path.exists(html_path):
            file_size = os.path.getsize(html_path)
            logger.info(f"HTML existe: {html_path} ({file_size} bytes)")
            
            with open(html_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename="relatorio_financeiro.html",
                    caption="📄 <b>Versão HTML</b> - Abra no navegador",
                    parse_mode="HTML"
                )
        else:
            logger.error(f"HTML não encontrado: {html_path}")
        
        # Verificar se PDF existe
        pdf_path = result.get('pdf')
        if pdf_path:
            logger.info(f"Tentando enviar PDF: {pdf_path}")
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(f"PDF existe: {pdf_path} ({file_size} bytes)")
                
                if file_size > 0:
                    with open(pdf_path, "rb") as f:
                        await update.message.reply_document(
                            document=f,
                            filename="relatorio_financeiro.pdf",
                            caption="📕 <b>Versão PDF</b> - Pronto para imprimir!",
                            parse_mode="HTML"
                        )
                    logger.info("PDF enviado com sucesso!")
                else:
                    logger.error("PDF existe mas está vazio (0 bytes)")
                    await update.message.reply_text(
                        "⚠️ PDF gerado mas está vazio. Use a versão HTML.",
                        reply_markup=menu
                    )
            else:
                logger.error(f"PDF não encontrado no caminho: {pdf_path}")
                await update.message.reply_text(
                    "💡 <i>PDF não foi salvo corretamente.</i>\n"
                    "Use a versão HTML acima!",
                    reply_markup=menu,
                    parse_mode="HTML"
                )
        else:
            logger.warning("PDF_PATH é None - PDF não foi gerado")
            await update.message.reply_text(
                "💡 <i>PDF não pôde ser gerado.</i>\n"
                "Use a versão HTML acima!",
                reply_markup=menu,
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ Ops! Deu um probleminha ao gerar o relatório.\n"
            f"Erro: {str(e)[:100]}",
            reply_markup=menu
        )


# ==============================
# PROCESSAMENTO INTELIGENTE COM FALLBACK GPT
# ==============================

async def handle_natural_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, intent: str = None):
    """Processa interações naturais baseadas na intenção detectada."""
    if intent is None:
        intent = detect_intent(message)
    
    # Se detectou intenção conhecida, responde naturalmente
    if intent != 'unknown' and intent in NATURAL_RESPONSES:
        response = get_natural_response(intent)
        if response:
            await update.message.reply_text(response, reply_markup=menu, parse_mode="HTML")
            return True
    
    return False


async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """Processa mensagem como transação financeira com fallback GPT."""
    user_id = str(update.effective_user.id)
    
    try:
        data = categorize_transaction(user_message)
        logger.info(f"GPT resposta: {data}")

        # Validações
        if not data or not isinstance(data, dict):
            raise ValueError("Resposta inválida")
            
        required_fields = ["type", "amount", "category"]
        if not all(field in data for field in required_fields):
            raise ValueError("Campos faltando")
            
        type_ = data["type"]
        amount = float(data["amount"])
        category = data["category"]
        
        if amount <= 0:
            raise ValueError("Valor inválido")
            
        if type_ not in ["income", "expense"]:
            raise ValueError("Tipo inválido")

    except Exception as e:
        logger.warning(f"Não é transação: '{user_message}' - {e}")
        
        # ===== FALLBACK INTELIGENTE COM GPT =====
        # 1. Tentar detectar com regex primeiro
        intent = detect_intent(user_message)
        
        if intent != 'unknown':
            if await handle_natural_interaction(update, context, user_message, intent):
                return
        
        # 2. Se regex falhar, usar GPT para classificar intenção
        logger.info(f"Regex falhou, tentando GPT para: '{user_message}'")
        gpt_result = classify_intent_with_gpt(user_message)
        
        gpt_intent = gpt_result.get('intent', 'unknown')
        confidence = gpt_result.get('confidence', 0.0)
        
        # Só usar resultado do GPT se tiver confiança suficiente
        if confidence >= 0.7 and gpt_intent != 'unknown' and gpt_intent != 'transaction':
            logger.info(f"GPT detectou intenção: {gpt_intent} (confiança: {confidence})")
            if await handle_natural_interaction(update, context, user_message, gpt_intent):
                return
        
        # 3. Se GPT também falhar ou for transação inválida, responder amigavelmente
        response = get_natural_response('not_understood')
        await update.message.reply_text(response, reply_markup=menu, parse_mode="HTML")
        return

    # Registrar transação
    try:
        add_transaction(
            user_id=user_id,
            type=type_,
            amount=amount,
            category=category,
        )
    except Exception as e:
        logger.error(f"Erro ao salvar: {e}")
        await update.message.reply_text(
            "❌ Eita, deu erro ao salvar. Pode tentar de novo?",
            reply_markup=menu
        )
        return

    # Resposta de sucesso personalizada
    summary = get_month_summary(user_id)
    
    emoji = "🟢" if type_ == "income" else "🔴"
    tipo_text = "Receita" if type_ == "income" else "Despesa"
    
    # Mensagens de sucesso variadas
    success_msgs = [
        f"✅ <b>Registrado!</b> {emoji} {tipo_text}: {category}\n💵 R${format_currency(amount)}",
        f"✅ <b>Anotado!</b> {emoji} {tipo_text} em {category}: R${format_currency(amount)}",
        f"✅ <b>Salvo!</b> {emoji} {tipo_text} registrada: R${format_currency(amount)} ({category})",
    ]
    
    msg = random.choice(success_msgs) + "\n\n"
    msg += (
        f"📊 <b>Resumo do Mês:</b>\n"
        f"💰 Receitas: R${format_currency(summary['income'])}\n"
        f"💸 Despesas: R${format_currency(summary['expense'])}\n"
        f"📈 Saldo: R${format_currency(summary['balance'])}"
    )
    
    # Alertas contextuais
    if summary["balance"] < 0:
        msg += "\n\n🚨 <b>Atenção:</b> Saldo negativo! Cuidado com os gastos."
    elif summary["balance"] < summary["income"] * 0.1 and summary["income"] > 0:
        msg += "\n\n⚠️ <b>Cuidado:</b> Você já gastou mais de 90% da renda!"

    await update.message.reply_text(msg, reply_markup=menu, parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteador principal de mensagens."""
    user_message = update.message.text.strip()
    
    # Verificar comando do menu primeiro
    if user_message in MENU_OPTIONS:
        command = MENU_OPTIONS[user_message]
        handlers = {
            "dashboard": dashboard, "resumo": resumo, "extrato": extrato,
            "grafico": grafico, "ajuda": ajuda, "analise": analise, "relatorio": relatorio
        }
        await handlers[command](update, context)
        return
    
    # Tentar processar como transação ou interação natural (com fallback GPT)
    await handle_transaction(update, context, user_message)


# ==============================
# ERROR HANDLER
# ==============================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Tratamento global de erros."""
    logger.error(f"Erro: {context.error}", exc_info=True)
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "😅 Ops! Algo deu errado. Tenta de novo ou usa os botões abaixo!",
            reply_markup=menu
        )


# ==============================
# INICIALIZAÇÃO
# ==============================

def main():
    """Função principal."""
    logger.info("Inicializando banco de dados...")
    init_db()

    logger.info("Iniciando bot...")
    
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Handlers
    handlers = [
        CommandHandler("start", start), CommandHandler("resumo", resumo),
        CommandHandler("extrato", extrato), CommandHandler("dashboard", dashboard),
        CommandHandler("grafico", grafico), CommandHandler("ajuda", ajuda),
        CommandHandler("analise", analise), CommandHandler("relatorio", relatorio),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.add_error_handler(error_handler)

    logger.info("Bot rodando!")
    application.run_polling()


if __name__ == "__main__":
    main()