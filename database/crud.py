from sqlalchemy import func
from database.models import SessionLocal, Transaction


# ==============================
# ADICIONAR TRANSAÇÃO
# ==============================

def add_transaction(user_id, type, amount, category):

    db = SessionLocal()

    try:

        transaction = Transaction(
            user_id=str(user_id),
            type=type,
            amount=amount,
            category=category,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    finally:
        db.close()


# ==============================
# RESUMO DO MÊS
# ==============================

def get_month_summary(user_id):

    db = SessionLocal()

    try:

        income = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "income")
            .scalar()
        ) or 0

        expense = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "expense")
            .scalar()
        ) or 0

        balance = income - expense

        return {
            "income": float(income),
            "expense": float(expense),
            "balance": float(balance),
        }

    finally:
        db.close()


# ==============================
# ÚLTIMAS TRANSAÇÕES
# ==============================

def get_last_transactions(user_id, limit=5):

    db = SessionLocal()

    try:

        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == str(user_id))
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

        return transactions

    finally:
        db.close()


# ==============================
# DASHBOARD
# ==============================

def get_dashboard_data(user_id):

    db = SessionLocal()

    try:

        income = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "income")
            .scalar()
        ) or 0

        expense = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "expense")
            .scalar()
        ) or 0

        balance = income - expense

        total_transactions = (
            db.query(func.count(Transaction.id))
            .filter(Transaction.user_id == str(user_id))
            .scalar()
        )

        top_category = (
            db.query(
                Transaction.category,
                func.sum(Transaction.amount).label("total"),
            )
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "expense")
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
            .first()
        )

        return {
            "income": float(income),
            "expense": float(expense),
            "balance": float(balance),
            "total_transactions": total_transactions,
            "top_category": top_category,
        }

    finally:
        db.close()


# ==============================
# GRÁFICO
# ==============================

def get_expenses_by_category(user_id):

    db = SessionLocal()

    try:

        data = (
            db.query(
                Transaction.category,
                func.sum(Transaction.amount),
            )
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "expense")
            .group_by(Transaction.category)
            .all()
        )

        return data

    finally:
        db.close()


# ==============================
# ANÁLISE FINANCEIRA
# ==============================

def get_monthly_analysis(user_id):

    db = SessionLocal()

    try:

        expenses = (
            db.query(
                Transaction.category,
                func.sum(Transaction.amount).label("total"),
            )
            .filter(Transaction.user_id == str(user_id))
            .filter(Transaction.type == "expense")
            .group_by(Transaction.category)
            .all()
        )

        return expenses

    finally:
        db.close()