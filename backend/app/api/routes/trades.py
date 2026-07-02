"""Trade history routes: read history + sync trades made directly on the exchange."""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase
from app.models.schemas import TradeOut
from app.services import exchange_service

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeOut])
def list_trades(
    user_id: str = Depends(get_current_user_id),
    strategy_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    query = (
        get_supabase()
        .table("trades")
        .select("*")
        .eq("user_id", user_id)
    )
    if strategy_id:
        query = query.eq("strategy_id", strategy_id)
    resp = query.order("executed_at", desc=True).limit(limit).execute()
    return resp.data


@router.post("/sync")
def sync_trades(user_id: str = Depends(get_current_user_id)):
    """Import recent trades made directly on the user's exchanges (read-only).

    Deduplicated on (user_id, ext_id) so re-syncing is safe. Non-custodial:
    only reads trade history, never places or withdraws anything.
    """
    sb = get_supabase()
    conns = (
        sb.table("exchange_connections").select("*").eq("user_id", user_id).execute()
    ).data or []

    rows = []
    errors = []
    for conn in conns:
        label = f"{conn['exchange']} ••••{conn.get('api_key_hint', '')}"
        try:
            client = exchange_service.client_from_connection(conn)
        except Exception:
            errors.append(f"{label} : clé API invalide (à supprimer / reconnecter).")
            continue

        fetched = []
        for fn, perm in (
            (exchange_service.fetch_recent_trades, "« Consulter les ordres et transactions clôturés »"),
            (exchange_service.fetch_ledger_trades, "« Consulter le registre »"),
        ):
            try:
                fetched.extend(fn(client))
            except Exception as exc:
                msg = str(exc)
                if "Permission denied" in msg or "PermissionDenied" in msg:
                    errors.append(f"{label} : permission {perm} manquante sur ta clé.")
                else:
                    errors.append(f"{label} : {msg[:120]}")

        for t in fetched:
            if not t.get("ext_id") or t.get("amount") is None:
                continue
            rows.append({
                "user_id": user_id,
                "strategy_id": None,
                "source": "exchange",
                "exchange": conn["exchange"],
                "ext_id": t["ext_id"],
                "symbol": t["symbol"],
                "quote_currency": t["quote_currency"],
                "side": t["side"],
                "amount": t["amount"],
                "filled": t["filled"],
                "price": t["price"],
                "status": "success",
                "executed_at": t["executed_at"],
            })

    imported = 0
    if rows:
        existing = (
            sb.table("trades")
            .select("ext_id")
            .eq("user_id", user_id)
            .not_.is_("ext_id", "null")
            .execute()
        ).data or []
        seen = {e["ext_id"] for e in existing}
        new_rows = [r for r in rows if r["ext_id"] not in seen]
        if new_rows:
            sb.table("trades").insert(new_rows).execute()
        imported = len(new_rows)

    return {"imported": imported, "fetched": len(rows), "errors": errors}
