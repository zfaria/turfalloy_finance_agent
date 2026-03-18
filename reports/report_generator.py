from database.crud import get_last_transactions
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import os
import base64
import re
import logging
import shutil

from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# =========================
# PDF DETECTION
# =========================

PDF_AVAILABLE = False
PDF_METHOD = None
PDF_ERROR = None

try:
    import pdfkit

    if shutil.which("wkhtmltopdf"):
        PDF_AVAILABLE = True
        PDF_METHOD = "pdfkit"
        logger.info("✅ wkhtmltopdf encontrado - PDF habilitado")
    else:
        PDF_ERROR = "wkhtmltopdf não instalado"
        logger.warning("⚠️ wkhtmltopdf não encontrado")

except ImportError as e:
    PDF_ERROR = str(e)
    logger.warning(f"⚠️ pdfkit não disponível: {e}")


# =========================
# HELPERS
# =========================

def sanitize_filename(value):
    """Remove caracteres inválidos para nome de arquivo"""
    return re.sub(r'[^\w\-_]', '_', str(value))


def format_currency(value):
    """Formata valor em moeda brasileira"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def image_to_base64(path):
    """Converte imagem para base64 para embed no HTML"""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Erro ao converter imagem para base64: {e}")
        return None


# =========================
# GRÁFICO DE CATEGORIAS (CORES VARIADAS)
# =========================

def generate_category_chart(categories, user_id):
    """
    Gera gráfico de barras horizontais com cores variadas - MAIOR NO TOPO.
    """
    if not categories:
        return "<p style='text-align:center;color:#7f8c8d;padding:40px;'>Sem despesas registradas no período.</p>"

    safe_id = sanitize_filename(user_id)
    path = f"reports/categories_{safe_id}.png"
    
    # Ordenar por valor DECRESCENTE (maior primeiro)
    sorted_items = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    # Pegar top 10 ou agrupar resto em "Outros" e inserir na posição correta
    if len(sorted_items) > 10:
        top = sorted_items[:10]
        others_value = sum(v for _, v in sorted_items[10:])
        # Inserir "Outros" na posição correta mantendo a ordem decrescente
        final = []
        inserted = False
        for cat, val in top:
            if not inserted and others_value > val:
                final.append(("Outros", others_value))
                inserted = True
            final.append((cat, val))
        if not inserted:
            final.append(("Outros", others_value))
    else:
        final = sorted_items
    
    labels = [x[0] for x in final]
    values = [x[1] for x in final]
    
    # Cores vibrantes
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
              '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#16a085', '#7f8c8d']
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Inverter ordem para plotar (matplotlib desenha de baixo pra cima)
    labels_plot = labels[::-1]
    values_plot = values[::-1]
    colors_plot = colors[:len(labels)][::-1]
    
    bars = ax.barh(labels_plot, values_plot, color=colors_plot, edgecolor='white', linewidth=1)
    
    # Adicionar valores nas barras
    for bar, val in zip(bars, values_plot):
        width = bar.get_width()
        ax.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2, 
                f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                va='center', ha='left', fontsize=10, fontweight='bold', color='#2c3e50')
    
    # Estilo limpo
    ax.set_xlim(0, max(values) * 1.25)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.tick_params(colors='#555', labelsize=10)
    ax.set_xlabel('Valor (R$)', color='#7f8c8d', fontsize=11)
    
    # Título
    ax.set_title('Top Categorias de Gasto', fontsize=16, fontweight='bold', 
                 color='#2c3e50', pad=20)
    
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    img = image_to_base64(path)
    
    if img:
        return f'<img class="chart" src="data:image/png;base64,{img}" alt="Gastos por Categoria">'
    return "<p>Erro ao gerar gráfico.</p>"


# =========================
# GRÁFICO DE EVOLUÇÃO (ÁREA VERDE)
# =========================

def generate_flow_chart(transactions, user_id):
    """
    Gera gráfico de área/linha para evolução do saldo (estilo da imagem).
    """
    if not transactions or len(transactions) < 2:
        return "<p style='text-align:center;color:#7f8c8d;padding:40px;'>Dados insuficientes.</p>"

    safe_id = sanitize_filename(user_id)
    path = f"reports/flow_{safe_id}.png"
    
    # Ordenar transações por data
    tx_sorted = sorted(transactions, key=lambda x: x.created_at)
    
    dates = []
    balances = []
    running = 0
    
    for t in tx_sorted:
        if t.type == "income":
            running += t.amount
        else:
            running -= t.amount
        
        dates.append(t.created_at.strftime("%d/%m"))
        balances.append(running)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Preencher área abaixo da linha (verde claro)
    ax.fill_between(range(len(dates)), balances, alpha=0.3, color='#27ae60')
    
    # Linha principal (verde escuro)
    ax.plot(range(len(dates)), balances, linewidth=2, color='#27ae60')
    
    # Linha de zero
    ax.axhline(y=0, color='#95a5a6', linestyle='-', linewidth=0.5, alpha=0.5)
    
    # Estilo limpo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.tick_params(colors='#555', labelsize=8)
    ax.set_ylabel('Saldo Acumulado (R$)', color='#7f8c8d', fontsize=10)
    ax.set_xlabel('Data', color='#7f8c8d', fontsize=10)
    
    # Título
    ax.set_title('Evolução do Saldo (últimos 30 dias)', fontsize=12, fontweight='bold', 
                 color='#2c3e50', pad=15)
    
    # Mostrar menos labels no eixo X para não ficar poluído
    step = max(1, len(dates) // 6)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    img = image_to_base64(path)
    
    if img:
        return f'<img class="chart" src="data:image/png;base64,{img}" alt="Evolução do Saldo">'
    return "<p>Erro ao gerar gráfico.</p>"


# =========================
# HTML COMPLETO (LAYOUT DAS IMAGENS)
# =========================

def generate_html(income, expense, balance, rows, cat_chart, flow_chart, 
                  analysis_html, report_date=None):
    """
    Gera o HTML completo com o layout das imagens enviadas.
    """
    if report_date is None:
        report_date = datetime.now().strftime("%d/%m/%Y")
    
    # Cor do saldo
    balance_color_class = "positive" if balance >= 0 else "negative"
    balance_signal = "+" if balance > 0 else ""
    
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Financeiro</title>
    <style>
        @page {{
            size: A4;
            margin: 10mm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f6fa;
            padding: 20px;
            color: #2c3e50;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        
        /* Header */
        .header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 25px;
        }}
        
        .header-icon {{
            font-size: 1.5em;
        }}
        
        .header h1 {{
            font-size: 1.8em;
            color: #2c3e50;
            font-weight: 600;
        }}
        
        /* Cards Section */
        .section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1em;
            color: #555;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .summary-cards {{
            display: flex;
            gap: 15px;
            justify-content: space-between;
        }}
        
        .summary-card {{
            flex: 1;
            text-align: center;
            padding: 15px;
            border-radius: 6px;
            min-width: 150px;
        }}
        
        .summary-card.income {{
            background: #d4edda;
        }}
        
        .summary-card.expense {{
            background: #f8d7da;
        }}
        
        .summary-card.balance {{
            background: #d1ecf1;
        }}
        
        .summary-card .label {{
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        .summary-card.income .label {{ color: #155724; }}
        .summary-card.expense .label {{ color: #721c24; }}
        .summary-card.balance .label {{ color: #0c5460; }}
        
        .summary-card .value {{
            font-size: 1.4em;
            font-weight: 700;
        }}
        
        .summary-card.income .value {{ color: #155724; }}
        .summary-card.expense .value {{ color: #721c24; }}
        .summary-card.balance .value {{ color: #0c5460; }}
        
        /* Charts */
        .chart-container {{
            text-align: center;
            padding: 10px;
        }}
        
        .chart {{
            max-width: 100%;
            height: auto;
        }}
        
        /* Table */
        .transactions-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        
        .transactions-table th {{
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #dee2e6;
            color: #495057;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        
        .transactions-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
            color: #555;
        }}
        
        .transactions-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .badge.receita {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.despesa {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .amount {{
            font-weight: 600;
            font-family: 'Courier New', monospace;
        }}
        
        .amount.receita {{ color: #155724; }}
        .amount.despesa {{ color: #721c24; }}
        
        /* Analysis Section */
        .analysis-box {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        
        .analysis-item {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 10px;
            font-size: 0.95em;
        }}
        
        .analysis-item:last-child {{
            margin-bottom: 0;
        }}
        
        .analysis-icon {{
            font-size: 1.2em;
        }}
        
        .analysis-text {{
            color: #555;
        }}
        
        .analysis-text strong {{
            color: #2c3e50;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            color: #7f8c8d;
            font-size: 0.85em;
            margin-top: 30px;
            padding: 20px;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .section {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <span class="header-icon">📊</span>
            <h1>Relatório Financeiro</h1>
        </div>
        
        <!-- Resumo do Período -->
        <div class="section">
            <div class="section-title">Resumo do Período</div>
            <div class="summary-cards">
                <div class="summary-card income">
                    <div class="label">Receitas</div>
                    <div class="value">R$ {format_currency(income)}</div>
                </div>
                <div class="summary-card expense">
                    <div class="label">Despesas</div>
                    <div class="value">R$ {format_currency(expense)}</div>
                </div>
                <div class="summary-card balance">
                    <div class="label">Saldo</div>
                    <div class="value">R$ {format_currency(balance)}</div>
                </div>
            </div>
        </div>
        
        <!-- Distribuição de Gastos -->
        <div class="section">
            <div class="section-title">Distribuição de Gastos</div>
            <div class="chart-container">
                {cat_chart}
            </div>
        </div>
        
        <!-- Evolução Financeira -->
        <div class="section">
            <div class="section-title">Evolução Financeira</div>
            <div class="chart-container">
                {flow_chart}
            </div>
        </div>
        
        <!-- Transações -->
        <div class="section page-break">
            <div class="section-title">Histórico de Transações</div>
            <table class="transactions-table">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Categoria</th>
                        <th>Tipo</th>
                        <th style="text-align: right;">Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        
        <!-- Análise -->
        <div class="section">
            <div class="section-title">Análise</div>
            {analysis_html}
        </div>
        
        <div class="footer">
            <p>Relatório gerado em {report_date}</p>
        </div>
    </div>
</body>
</html>"""


# =========================
# GERAR ANÁLISE
# =========================

def generate_analysis(income, expense, balance, categories):
    """Gera HTML com análise e insights."""
    
    lines = []
    
    # Análise do saldo
    if balance > 0:
        lines.append(f'<div class="analysis-item"><span class="analysis-icon">✅</span><div class="analysis-text"><strong>Situação positiva!</strong> Você economizou R$ {format_currency(balance)} neste período.</div></div>')
    elif balance < 0:
        lines.append(f'<div class="analysis-item"><span class="analysis-icon">⚠️</span><div class="analysis-text"><strong>Atenção!</strong> Você gastou R$ {format_currency(abs(balance))} a mais do que recebeu.</div></div>')
    else:
        lines.append(f'<div class="analysis-item"><span class="analysis-icon">⚖️</span><div class="analysis-text">Seu saldo está equilibrado neste período.</div></div>')
    
    # Maior despesa
    if categories:
        top_category = max(categories.items(), key=lambda x: x[1])
        total_expense = sum(categories.values())
        percentage = (top_category[1] / total_expense * 100) if total_expense > 0 else 0
        
        lines.append(f'<div class="analysis-item"><span class="analysis-icon">💡</span><div class="analysis-text"><strong>Dica:</strong> Sua maior despesa foi com <strong>{top_category[0]}</strong> (R$ {format_currency(top_category[1])}), representando {percentage:.1f}% dos gastos totais.</div></div>')
    
    return f'<div class="analysis-box">{"".join(lines)}</div>'


# =========================
# MAIN
# =========================

def generate_html_report(user_id, generate_pdf=True):
    """
    Gera relatório financeiro em HTML e opcionalmente PDF.
    """
    os.makedirs("reports", exist_ok=True)
    
    # Buscar transações
    transactions = get_last_transactions(user_id, limit=200)
    
    # Calcular totais
    income = 0
    expense = 0
    rows = ""
    categories = {}
    
    # Ordenar por data decrescente (mais recente primeiro) para a tabela
    transactions_sorted = sorted(transactions, key=lambda x: x.created_at, reverse=True)
    
    for t in transactions_sorted:
        date = t.created_at.strftime("%d/%m/%Y")
        type_label = "receita" if t.type == "income" else "despesa"
        badge_class = "receita" if t.type == "income" else "despesa"
        amount_class = "receita" if t.type == "income" else "despesa"
        
        rows += f"""
        <tr>
            <td>{date}</td>
            <td>{t.category}</td>
            <td><span class="badge {badge_class}">{type_label.capitalize()}</span></td>
            <td style="text-align: right;" class="amount {amount_class}">R$ {format_currency(t.amount)}</td>
        </tr>
        """
        
        if t.type == "income":
            income += t.amount
        else:
            expense += t.amount
            categories[t.category] = categories.get(t.category, 0) + t.amount
    
    balance = income - expense
    
    # Gerar gráficos (usar transações na ordem cronológica para os gráficos)
    cat_chart = generate_category_chart(categories, user_id)
    flow_chart = generate_flow_chart(transactions, user_id)
    
    # Gerar análise
    analysis_html = generate_analysis(income, expense, balance, categories)
    
    # Gerar HTML
    html = generate_html(income, expense, balance, rows, cat_chart, flow_chart, analysis_html)
    
    # Salvar HTML
    safe_id = sanitize_filename(user_id)
    html_path = f"reports/report_{safe_id}.html"
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    logger.info(f"✅ HTML gerado: {html_path}")
    
    # Gerar PDF se disponível
    pdf_path = None
    
    if generate_pdf and PDF_AVAILABLE:
        try:
            pdf_path = f"reports/report_{safe_id}.pdf"
            
            options = {
                'page-size': 'A4',
                'encoding': 'UTF-8',
                'quiet': '',
                'enable-local-file-access': '',
                'print-media-type': '',
                'margin-top': '0',
                'margin-right': '0',
                'margin-bottom': '0',
                'margin-left': '0'
            }
            
            pdfkit.from_string(html, pdf_path, options=options)
            logger.info(f"✅ PDF gerado: {pdf_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF: {e}")
            pdf_path = None
    
    return {
        "html": html_path,
        "pdf": pdf_path,
        "income": income,
        "expense": expense,
        "balance": balance
    }


if __name__ == "__main__":
    print("Report Generator carregado com sucesso!")
    print(f"PDF disponível: {PDF_AVAILABLE}")