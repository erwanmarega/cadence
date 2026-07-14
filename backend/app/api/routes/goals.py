"""Savings goals: track progress toward "reach X € in <crypto>".

Progress = current value of the matching asset in the user's portfolio,
relative to the target. Purely a savings/motivation feature — never advice.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.routes.portfolio import compute_positions
from app.core.deps import get_current_user_id
from app.db.supabase import get_supabase

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalCreate(BaseModel):
    base: str = Field(min_length=2, max_length=10)
    target_amount: float = Field(gt=0)
    quote_currency: str = Field(default="EUR", min_length=3, max_length=5)
    title: Optional[str] = None

    @field_validator("base")
    @classmethod
    def upper_base(cls, v: str) -> str:
        return v.upper()


class GoalUpdate(BaseModel):
    base: Optional[str] = Field(default=None, min_length=2, max_length=10)
    target_amount: Optional[float] = Field(default=None, gt=0)
    quote_currency: Optional[str] = Field(default=None, min_length=3, max_length=5)
    title: Optional[str] = None

    @field_validator("base")
    @classmethod
    def upper_base(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


class GoalOut(BaseModel):
    id: str
    base: str
    quote_currency: str
    target_amount: float
    title: Optional[str] = None
    current_value: float
    progress_pct: float
    created_at: datetime


def _attach_progress(goals: list[dict], user_id: str) -> list[dict]:
    pos = {p["base"]: p for p in compute_positions(user_id)["positions"]}
    out = []
    for g in goals:
        p = pos.get(g["base"])

        current = 0.0
        if p:
            current = p["current_value"] if p["current_value"] is not None else p["invested"]
        pct = round(min(current / g["target_amount"] * 100, 100), 1) if g["target_amount"] else 0.0
        out.append({**g, "current_value": round(current, 2), "progress_pct": pct})
    return out


@router.get("", response_model=list[GoalOut])
def list_goals(user_id: str = Depends(get_current_user_id)):
    goals = (
        get_supabase()
        .table("goals")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    ).data or []
    return _attach_progress(goals, user_id)


@router.post("", response_model=GoalOut, status_code=201)
def create_goal(body: GoalCreate, user_id: str = Depends(get_current_user_id)):
    row = {
        "user_id": user_id,
        "base": body.base,
        "quote_currency": body.quote_currency.upper(),
        "target_amount": body.target_amount,
        "title": body.title,
    }
    created = get_supabase().table("goals").insert(row).execute().data[0]
    return _attach_progress([created], user_id)[0]


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    body: GoalUpdate,
    user_id: str = Depends(get_current_user_id),
):
    fields = body.model_dump(exclude_unset=True)
    if "quote_currency" in fields and fields["quote_currency"]:
        fields["quote_currency"] = fields["quote_currency"].upper()
    if not fields:
        raise HTTPException(status_code=400, detail="Aucune modification fournie.")

    updated = (
        get_supabase()
        .table("goals")
        .update(fields)
        .eq("id", goal_id)
        .eq("user_id", user_id)
        .execute()
    ).data
    if not updated:
        raise HTTPException(status_code=404, detail="Objectif introuvable.")
    return _attach_progress([updated[0]], user_id)[0]


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, user_id: str = Depends(get_current_user_id)):
    get_supabase().table("goals").delete().eq("id", goal_id).eq("user_id", user_id).execute()
