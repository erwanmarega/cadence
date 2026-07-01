"""Exchange connection routes.

Stores exchange API keys ENCRYPTED at rest. Validates keys with a
read-only call before saving. Never returns the key material — only a
4-char hint.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user_id
from app.core.security import encrypt
from app.db.supabase import get_supabase
from app.models.schemas import ExchangeConnectionCreate, ExchangeConnectionOut
from app.services import exchange_service

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


@router.post("", response_model=ExchangeConnectionOut, status_code=201)
def connect_exchange(
    body: ExchangeConnectionCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        exchange_service.verify_credentials(
            body.exchange, body.api_key, body.api_secret, body.passphrase
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not authenticate with {body.exchange.value}: {exc}",
        ) from exc

    row = {
        "user_id": user_id,
        "exchange": body.exchange.value,
        "api_key_enc": encrypt(body.api_key),
        "api_secret_enc": encrypt(body.api_secret),
        "passphrase_enc": encrypt(body.passphrase) if body.passphrase else None,
        "api_key_hint": body.api_key[-4:],
    }
    resp = get_supabase().table("exchange_connections").insert(row).execute()
    return _to_out(resp.data[0])


@router.get("", response_model=list[ExchangeConnectionOut])
def list_exchanges(user_id: str = Depends(get_current_user_id)):
    resp = (
        get_supabase()
        .table("exchange_connections")
        .select("id, exchange, api_key_hint, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_out(r) for r in resp.data]


@router.delete("/{connection_id}", status_code=204)
def delete_exchange(connection_id: str, user_id: str = Depends(get_current_user_id)):
    (
        get_supabase()
        .table("exchange_connections")
        .delete()
        .eq("id", connection_id)
        .eq("user_id", user_id)
        .execute()
    )


def _to_out(row: dict) -> ExchangeConnectionOut:
    return ExchangeConnectionOut(
        id=row["id"],
        exchange=row["exchange"],
        api_key_hint=row["api_key_hint"],
        created_at=row["created_at"],
    )
