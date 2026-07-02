"""Relevé fiscal informatif — export des achats DCA et du prix de revient.

Cadence n'effectue que des achats : aucune cession n'est déclenchée par
l'app, donc aucune plus-value imposable n'est générée ici. Ce module fournit
un relevé factuel des acquisitions (dates, montants, prix de revient) à
conserver par l'utilisateur. Il ne calcule PAS la plus-value imposable : le
calcul officiel (formulaire 2086, art. 150 VH bis du CGI) nécessite la valeur
de l'ensemble du portefeuille crypto au moment de la cession, y compris hors
Cadence. Information, pas conseil fiscal.
"""

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(prefix="/tax", tags=["tax"])

NOTICE = [
    "Relevé fiscal informatif — Cadence",
    "Cadence n'effectue que des achats. Aucune vente n'est déclenchée par l'app, donc aucune plus-value imposable n'est générée ici.",
    "En France, la plus-value sur actifs numériques n'est imposable qu'à la cession (vente en euros, achat d'un bien, ou paiement). Conserve ce relevé pour le jour où tu vendras.",
    "Le calcul officiel de la plus-value (formulaire 2086, art. 150 VH bis du CGI) nécessite la valeur de TON portefeuille crypto entier au moment de la cession, y compris hors Cadence. Ce document ne le calcule pas.",
    "Frais de transaction non inclus dans ce relevé.",
    "Information factuelle, pas un conseil fiscal. En cas de doute, rapproche-toi d'un professionnel.",
]


def _exchange_map(user_id: str) -> dict[str, str]:
    sb = get_supabase()
    strats = (
        sb.table("strategies")
        .select("id, exchange_connection_id")
        .eq("user_id", user_id)
        .execute()
    ).data or []
    conns = (
        sb.table("exchange_connections")
        .select("id, exchange")
        .eq("user_id", user_id)
        .execute()
    ).data or []
    conn_ex = {c["id"]: c["exchange"] for c in conns}
    return {s["id"]: conn_ex.get(s["exchange_connection_id"], "—") for s in strats}


def _success_trades(user_id: str, year: int | None = None) -> list[dict]:
    sb = get_supabase()
    query = (
        sb.table("trades")
        .select("symbol, amount, filled, price, quote_currency, executed_at, strategy_id, side, source, exchange")
        .eq("user_id", user_id)
        .eq("status", "success")
    )
    if year is not None:
        query = query.gte("executed_at", f"{year}-01-01T00:00:00+00:00").lt(
            "executed_at", f"{year + 1}-01-01T00:00:00+00:00"
        )
    return (query.order("executed_at").execute()).data or []


def _available_years(user_id: str) -> list[int]:
    trades = _success_trades(user_id)
    return sorted({int(t["executed_at"][:4]) for t in trades if t.get("executed_at")}, reverse=True)


def _build(user_id: str, year: int) -> dict:
    trades = [t for t in _success_trades(user_id, year) if t.get("filled") and t.get("side") != "sell"]
    exmap = _exchange_map(user_id)

    rows = []
    agg: dict[str, dict] = {}
    total_invested = 0.0
    quote = "EUR"

    for t in trades:
        quote = t.get("quote_currency") or quote
        base = t["symbol"].split("/")[0]
        invested = float(t["amount"])
        filled = float(t["filled"])
        total_invested += invested
        rows.append(
            {
                "date": t["executed_at"][:10],
                "exchange": t.get("exchange") or exmap.get(t.get("strategy_id"), "—"),
                "base": base,
                "symbol": t["symbol"],
                "invested": round(invested, 2),
                "filled": filled,
                "price": round(float(t["price"]), 2) if t.get("price") else None,
            }
        )
        a = agg.setdefault(base, {"base": base, "buys": 0, "invested": 0.0, "quantity": 0.0})
        a["buys"] += 1
        a["invested"] += invested
        a["quantity"] += filled

    assets = []
    for a in agg.values():
        assets.append(
            {
                "base": a["base"],
                "buys": a["buys"],
                "invested": round(a["invested"], 2),
                "quantity": round(a["quantity"], 8),
                "avg_price": round(a["invested"] / a["quantity"], 2) if a["quantity"] else None,
            }
        )

    return {
        "year": year,
        "quote": quote,
        "buys": len(rows),
        "total_invested": round(total_invested, 2),
        "assets": sorted(assets, key=lambda x: x["invested"], reverse=True),
        "rows": rows,
    }


@router.get("/summary")
def summary(
    user_id: str = Depends(get_current_user_id),
    year: int | None = Query(default=None),
):
    years = _available_years(user_id)
    if not years:
        return {"years": [], "year": None, "quote": "EUR", "buys": 0, "total_invested": 0.0, "assets": []}
    target = year if year in years else years[0]
    data = _build(user_id, target)
    data["years"] = years
    data.pop("rows", None)
    return data


@router.get("/export")
def export_csv(
    user_id: str = Depends(get_current_user_id),
    year: int = Query(...),
):
    data = _build(user_id, year)

    buf = io.StringIO()
    buf.write("﻿")
    writer = csv.writer(buf, delimiter=";")

    for line in NOTICE:
        writer.writerow([line])
    writer.writerow([])

    writer.writerow([f"Achats {year} ({data['quote']})"])
    writer.writerow(["Date", "Exchange", "Opération", "Actif", "Montant investi", "Quantité reçue", "Prix unitaire"])
    for r in data["rows"]:
        writer.writerow([
            r["date"], r["exchange"], "Achat", r["base"],
            r["invested"], r["filled"], r["price"] if r["price"] is not None else "",
        ])
    writer.writerow([])

    writer.writerow(["Récapitulatif par actif — prix de revient"])
    writer.writerow(["Actif", "Nombre d'achats", "Total investi", "Quantité totale", "Prix de revient moyen"])
    for a in data["assets"]:
        writer.writerow([
            a["base"], a["buys"], a["invested"], a["quantity"],
            a["avg_price"] if a["avg_price"] is not None else "",
        ])
    writer.writerow([])
    writer.writerow(["Total investi", data["total_invested"]])

    buf.seek(0)
    filename = f"cadence_releve_fiscal_{year}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
