from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional
import logging

from database import db
from auth import get_current_admin
from models import CashWithdrawalCreate
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.get("/accounting/report")
async def get_accounting_report(
    gym_id: Optional[str] = None, date_from: Optional[str] = None,
    date_to: Optional[str] = None, admin: dict = Depends(get_current_admin)
):
    query = {"payment_status": "paid"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    # Include POS sales
    pos_query = {}
    if admin["role"] != "super_admin":
        pos_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        pos_query["gym_id"] = gym_id
    if date_from:
        pos_query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in pos_query:
            pos_query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            pos_query["created_at"] = {"$lte": date_to + "T23:59:59"}
    pos_sales = await db.pos_sales.find(pos_query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    # Cash withdrawals
    withdrawal_query = {}
    if admin["role"] != "super_admin":
        withdrawal_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        withdrawal_query["gym_id"] = gym_id
    if date_from:
        withdrawal_query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in withdrawal_query:
            withdrawal_query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            withdrawal_query["created_at"] = {"$lte": date_to + "T23:59:59"}
    withdrawals = await db.cash_withdrawals.find(withdrawal_query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    total_revenue = sum(t.get("amount", 0) for t in transactions)
    cash_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") == "cash")
    card_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") == "card_reception")
    stripe_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") in (None, "stripe"))
    mercadopago_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") == "mercadopago")
    
    pos_revenue = sum(s.get("total", 0) for s in pos_sales)
    pos_cash = sum(s.get("total", 0) for s in pos_sales if s.get("payment_method") == "cash")
    pos_card = sum(s.get("total", 0) for s in pos_sales if s.get("payment_method") == "card")
    
    total_withdrawals = sum(w.get("amount", 0) for w in withdrawals)
    
    daily_revenue = {}
    for t in transactions:
        date_key = t.get("created_at", "")[:10]
        if date_key:
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + t.get("amount", 0)
    for s in pos_sales:
        date_key = s.get("created_at", "")[:10]
        if date_key:
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + s.get("total", 0)
    
    daily_chart = [{"date": k, "amount": v} for k, v in sorted(daily_revenue.items())]
    
    return {
        "transactions": transactions,
        "pos_sales": pos_sales,
        "withdrawals": withdrawals,
        "summary": {
            "total_revenue": total_revenue + pos_revenue,
            "membership_revenue": total_revenue,
            "pos_revenue": pos_revenue,
            "total_transactions": len(transactions) + len(pos_sales),
            "cash_total": cash_total + pos_cash,
            "card_total": card_total + pos_card,
            "stripe_total": stripe_total,
            "mercadopago_total": mercadopago_total,
            "total_withdrawals": total_withdrawals,
            "net_cash": cash_total + pos_cash - total_withdrawals,
        },
        "daily_chart": daily_chart
    }

@router.post("/accounting/withdrawal")
async def create_cash_withdrawal(withdrawal: CashWithdrawalCreate, admin: dict = Depends(get_current_admin)):
    from auth import check_role
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    withdrawal_dict = {
        "id": str(uuid.uuid4()),
        "gym_id": withdrawal.gym_id,
        "amount": withdrawal.amount,
        "reason": withdrawal.reason,
        "notes": withdrawal.notes,
        "registered_by": admin["id"],
        "registered_by_name": admin.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cash_withdrawals.insert_one(withdrawal_dict)
    withdrawal_dict.pop("_id", None)
    return withdrawal_dict

@router.get("/accounting/withdrawals")
async def get_cash_withdrawals(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    withdrawals = await db.cash_withdrawals.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return withdrawals

@router.get("/accounting/transactions")
async def get_all_transactions(
    gym_id: Optional[str] = None, status: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get all transactions with paid/pending status for detailed view"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if status:
        query["payment_status"] = status
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    # Enrich with member data
    for t in transactions:
        if t.get("member_id") and not t.get("member_name"):
            member = await db.members.find_one({"id": t["member_id"]}, {"_id": 0, "name": 1, "code": 1})
            if member:
                t["member_name"] = member.get("name")
                t["member_code"] = member.get("code")
        if t.get("plan_id") and not t.get("plan_name"):
            plan = await db.plans.find_one({"id": t["plan_id"]}, {"_id": 0, "name": 1})
            if plan:
                t["plan_name"] = plan.get("name")
    paid_count = len([t for t in transactions if t.get("payment_status") == "paid"])
    pending_count = len([t for t in transactions if t.get("payment_status") == "pending"])
    total_paid = sum(t.get("amount", 0) for t in transactions if t.get("payment_status") == "paid")
    total_pending = sum(t.get("amount", 0) for t in transactions if t.get("payment_status") == "pending")
    return {
        "transactions": transactions,
        "summary": {
            "paid_count": paid_count,
            "pending_count": pending_count,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_count": len(transactions)
        }
    }


@router.delete("/accounting/prune")
async def prune_old_records(months: int = 6, admin: dict = Depends(get_current_admin)):
    from auth import check_role
    check_role(admin, ["super_admin", "gym_admin"])
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=months * 30)).isoformat()
    gym_id = admin.get("gym_id")
    query = {"created_at": {"$lt": cutoff}}
    if gym_id:
        query["gym_id"] = gym_id
    
    access_deleted = await db.access_logs.delete_many(query)
    
    log_query = {"timestamp": {"$lt": cutoff}}
    if gym_id:
        log_query["gym_id"] = gym_id
    access_log_deleted = await db.access_logs.delete_many(log_query)
    
    return {
        "message": f"Registros anteriores a {months} meses eliminados",
        "access_logs_deleted": access_deleted.deleted_count + access_log_deleted.deleted_count,
    }

@router.get("/accounting/pdf")
async def generate_accounting_pdf(
    gym_id: Optional[str] = None, date_from: Optional[str] = None,
    date_to: Optional[str] = None, admin: dict = Depends(get_current_admin)
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from io import BytesIO
    
    query = {"payment_status": "paid"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", 1).to_list(5000)
    gym_name = "Todos los Gimnasios"
    target_gym_id = admin.get("gym_id") or gym_id
    if target_gym_id:
        gym_doc = await db.gyms.find_one({"id": target_gym_id}, {"_id": 0, "name": 1})
        gym_name = gym_doc.get("name", gym_name) if gym_doc else gym_name
    total = sum(t.get("amount", 0) for t in transactions)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=6)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    elements = []
    elements.append(Paragraph(f"Informe de Contabilidad - {gym_name}", title_style))
    period = ""
    if date_from:
        period += f"Desde: {date_from} "
    if date_to:
        period += f"Hasta: {date_to}"
    if not period:
        period = "Todos los periodos"
    elements.append(Paragraph(period, subtitle_style))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"<b>Total Recaudado: ${total:,.2f}</b>  |  Transacciones: {len(transactions)}", styles['Normal']))
    elements.append(Spacer(1, 8*mm))
    if transactions:
        table_data = [['Fecha', 'Socio', 'Plan', 'Metodo', 'Monto']]
        for t in transactions:
            method_map = {"cash": "Efectivo", "card_reception": "Tarjeta", "stripe": "Stripe Online", "mercadopago": "MercadoPago"}
            method = method_map.get(t.get("payment_method", "stripe"), "Stripe Online")
            date_str = t.get("created_at", "")[:10]
            table_data.append([date_str, t.get("member_name", "-"), t.get("plan_name", "-"), method, f"${t.get('amount', 0):,.2f}"])
        col_widths = [70, 130, 100, 80, 70]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay transacciones en este periodo.", styles['Normal']))
    doc.build(elements)
    buffer.seek(0)
    filename = f"contabilidad_{gym_name.replace(' ', '_')}_{date_from or 'all'}_{date_to or 'all'}.pdf"
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/accounting/sales-report-pdf")
async def generate_sales_report_pdf(
    gym_id: Optional[str] = None, period: str = "daily",
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from io import BytesIO
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    if not date_from:
        if period == "daily":
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()[:10]
        elif period == "weekly":
            date_from = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()[:10]
        elif period == "monthly":
            date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()[:10]
        else:
            date_from = (now - timedelta(days=365)).isoformat()[:10]
    if not date_to:
        date_to = now.isoformat()[:10]
    
    target_gym_id = admin.get("gym_id") or gym_id
    
    # Membership payments
    pay_query = {"payment_status": "paid", "created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
    if target_gym_id:
        pay_query["gym_id"] = target_gym_id
    transactions = await db.payment_transactions.find(pay_query, {"_id": 0}).sort("created_at", 1).to_list(5000)
    
    # POS sales
    pos_query = {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
    if target_gym_id:
        pos_query["gym_id"] = target_gym_id
    pos_sales = await db.pos_sales.find(pos_query, {"_id": 0}).sort("created_at", 1).to_list(5000)
    
    # Withdrawals
    w_query = {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
    if target_gym_id:
        w_query["gym_id"] = target_gym_id
    withdrawals = await db.cash_withdrawals.find(w_query, {"_id": 0}).sort("created_at", 1).to_list(1000)
    
    gym_name = "Todos los Gimnasios"
    if target_gym_id:
        gym_doc = await db.gyms.find_one({"id": target_gym_id}, {"_id": 0, "name": 1})
        gym_name = gym_doc.get("name", gym_name) if gym_doc else gym_name
    
    total_memberships = sum(t.get("amount", 0) for t in transactions)
    total_pos = sum(s.get("total", 0) for s in pos_sales)
    total_withdrawals = sum(w.get("amount", 0) for w in withdrawals)
    grand_total = total_memberships + total_pos
    
    period_labels = {"daily": "Diario", "weekly": "Semanal", "monthly": "Mensual", "custom": "Personalizado"}
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=12*mm, rightMargin=12*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=16, spaceAfter=4, textColor=colors.HexColor('#18181B'))
    sub_style = ParagraphStyle('S', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    section_style = ParagraphStyle('Sec', parent=styles['Heading2'], fontSize=12, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor('#18181B'))
    
    elements = []
    elements.append(Paragraph(f"Informe de Ventas - {gym_name}", title_style))
    elements.append(Paragraph(f"Periodo: {period_labels.get(period, period)} | Desde: {date_from} | Hasta: {date_to}", sub_style))
    elements.append(Spacer(1, 6*mm))
    
    # Summary table
    summary_data = [
        ['Concepto', 'Total'],
        ['Ingresos por Membresias', f'${total_memberships:,.2f}'],
        ['Ingresos por Ventas POS', f'${total_pos:,.2f}'],
        ['TOTAL INGRESOS', f'${grand_total:,.2f}'],
        ['Retiros de Caja', f'-${total_withdrawals:,.2f}'],
        ['NETO', f'${(grand_total - total_withdrawals):,.2f}'],
    ]
    t = Table(summary_data, colWidths=[300, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#E8F5E9')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#E3F2FD')),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8*mm))
    
    # Memberships detail
    if transactions:
        elements.append(Paragraph("Detalle de Membresias", section_style))
        mem_data = [['Fecha', 'Socio', 'Plan', 'Metodo', 'Monto']]
        method_map = {"cash": "Efectivo", "card_reception": "Tarjeta", "stripe": "Stripe", "mercadopago": "MercadoPago"}
        for tx in transactions:
            mem_data.append([
                tx.get("created_at", "")[:10],
                tx.get("member_name", "-"),
                tx.get("plan_name", "-"),
                method_map.get(tx.get("payment_method", "stripe"), "Stripe"),
                f'${tx.get("amount", 0):,.2f}'
            ])
        mt = Table(mem_data, colWidths=[65, 130, 110, 75, 70])
        mt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(mt)
        elements.append(Spacer(1, 6*mm))
    
    # POS detail
    if pos_sales:
        elements.append(Paragraph("Detalle de Ventas POS", section_style))
        pos_data = [['Fecha', 'Productos', 'Metodo', 'Total']]
        for s in pos_sales:
            items_str = ", ".join([f"{i['product_name']}({i['quantity']})" for i in s.get("items", [])])
            pos_data.append([
                s.get("created_at", "")[:10],
                items_str[:50],
                "Efectivo" if s.get("payment_method") == "cash" else "Tarjeta",
                f'${s.get("total", 0):,.2f}'
            ])
        pt = Table(pos_data, colWidths=[65, 220, 75, 70])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(pt)
        elements.append(Spacer(1, 6*mm))
    
    # Withdrawals detail
    if withdrawals:
        elements.append(Paragraph("Detalle de Retiros de Caja", section_style))
        wd = [['Fecha', 'Motivo', 'Responsable', 'Monto']]
        for w in withdrawals:
            wd.append([w.get("created_at", "")[:10], w.get("reason", ""), w.get("registered_by_name", ""), f'-${w.get("amount", 0):,.2f}'])
        wt = Table(wd, colWidths=[65, 190, 110, 70])
        wt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (-1, 1), (-1, -1), colors.red),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(wt)
    
    doc.build(elements)
    buffer.seek(0)
    filename = f"informe_ventas_{period}_{gym_name.replace(' ','_')}_{date_from}_{date_to}.pdf"
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
