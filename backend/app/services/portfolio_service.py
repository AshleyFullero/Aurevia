"""
Portfolio Service
─────────────────
Business logic for session-based investment portfolio tracking.
Handles CRUD operations and portfolio-level financial aggregations.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioEntry
from app.models.property import Property
from app.schemas.portfolio import PortfolioEntryCreate, PortfolioEntryUpdate, PortfolioSummary
from app.schemas.property import PropertyResponse


class PortfolioService:
    """Business logic for portfolio CRUD and financial analysis."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Add Entry ──────────────────────────────────────────────────────────────
    async def add_entry(
        self,
        session_token: str,
        payload: PortfolioEntryCreate,
    ) -> PortfolioEntry:
        """Add a property to the session's portfolio. Raises ValueError on duplicates."""
        # Verify property exists
        prop = await self._get_property(payload.property_id)
        if prop is None:
            raise ValueError(f"Property with ID {payload.property_id} not found.")

        # Use list price as default purchase price if not provided
        purchase_price = payload.purchase_price or prop.list_price

        entry = PortfolioEntry(
            session_token=session_token,
            property_id=payload.property_id,
            purchase_price=purchase_price,
            purchase_date=payload.purchase_date,
            down_payment_pct=payload.down_payment_pct,
            mortgage_rate=payload.mortgage_rate,
            loan_term_years=payload.loan_term_years,
            actual_monthly_rent=payload.actual_monthly_rent,
            notes=payload.notes,
            status=payload.status,
        )
        self.db.add(entry)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("This property is already in your portfolio.")
        await self.db.refresh(entry)
        return entry

    # ── Update Entry ───────────────────────────────────────────────────────────
    async def update_entry(
        self,
        session_token: str,
        entry_id: int,
        payload: PortfolioEntryUpdate,
    ) -> Optional[PortfolioEntry]:
        """Update a portfolio entry. Returns None if not found."""
        entry = await self._get_entry(session_token, entry_id)
        if entry is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    # ── Remove Entry ───────────────────────────────────────────────────────────
    async def remove_entry(self, session_token: str, entry_id: int) -> bool:
        """Remove a portfolio entry. Returns True if deleted, False if not found."""
        entry = await self._get_entry(session_token, entry_id)
        if entry is None:
            return False
        await self.db.delete(entry)
        await self.db.commit()
        return True

    # ── List Entries ───────────────────────────────────────────────────────────
    async def list_entries(
        self,
        session_token: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return all portfolio entries for a session with full property detail
        and computed financial metrics.
        """
        stmt = (
            select(PortfolioEntry)
            .where(PortfolioEntry.session_token == session_token)
            .order_by(PortfolioEntry.created_at.desc())
        )
        if status:
            stmt = stmt.where(PortfolioEntry.status == status)

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        enriched = []
        for entry in entries:
            prop = await self._get_property(entry.property_id)
            enriched.append(self._build_entry_response(entry, prop))
        return enriched

    # ── Portfolio Summary ──────────────────────────────────────────────────────
    async def get_summary(self, session_token: str) -> PortfolioSummary:
        """Compute aggregate portfolio statistics for a session."""
        entries_data = await self.list_entries(session_token)

        active = [e for e in entries_data if e["status"] == "active"]
        total = len(entries_data)
        active_count = len(active)

        if not entries_data:
            return PortfolioSummary(
                session_token=session_token,
                total_entries=0,
                active_entries=0,
            )

        # Aggregate financials from active entries
        total_value = sum(e["purchase_price"] or 0 for e in active)
        total_equity = sum(e["equity_estimate"] or 0 for e in active)
        total_monthly_income = sum(e["monthly_income"] or 0 for e in active)
        total_monthly_mortgage = sum(e["monthly_mortgage_payment"] or 0 for e in active)
        total_monthly_cash_flow = sum(e["monthly_cash_flow"] or 0 for e in active)

        cap_rates = [e["cap_rate"] for e in active if e.get("cap_rate")]
        avg_cap_rate = sum(cap_rates) / len(cap_rates) if cap_rates else None

        risk_scores = [e["risk_score"] for e in active if e.get("risk_score") is not None]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else None

        # Weighted cash-on-cash
        coc_values = [e["cash_on_cash_return"] for e in active if e.get("cash_on_cash_return")]
        weighted_coc = sum(coc_values) / len(coc_values) if coc_values else None

        # Breakdowns
        by_type: Dict[str, int] = {}
        by_city: Dict[str, int] = {}
        for e in active:
            pt = e.get("property_type", "unknown")
            by_type[pt] = by_type.get(pt, 0) + 1
            city = e.get("city", "unknown")
            by_city[city] = by_city.get(city, 0) + 1

        return PortfolioSummary(
            session_token=session_token,
            total_entries=total,
            active_entries=active_count,
            total_portfolio_value=round(total_value) if total_value else None,
            total_portfolio_value_formatted=f"${total_value:,.0f}" if total_value else None,
            total_equity_estimate=round(total_equity) if total_equity else None,
            total_equity_formatted=f"${total_equity:,.0f}" if total_equity else None,
            total_monthly_income=round(total_monthly_income, 2) if total_monthly_income else None,
            total_monthly_income_formatted=f"${total_monthly_income:,.0f}" if total_monthly_income else None,
            total_annual_income=round(total_monthly_income * 12) if total_monthly_income else None,
            total_annual_income_formatted=f"${total_monthly_income * 12:,.0f}" if total_monthly_income else None,
            portfolio_avg_cap_rate=round(avg_cap_rate, 4) if avg_cap_rate else None,
            portfolio_avg_cap_rate_pct=f"{avg_cap_rate * 100:.1f}%" if avg_cap_rate else None,
            portfolio_weighted_cash_on_cash=round(weighted_coc, 4) if weighted_coc else None,
            portfolio_weighted_cash_on_cash_pct=f"{weighted_coc * 100:.1f}%" if weighted_coc else None,
            total_monthly_mortgage=round(total_monthly_mortgage, 2) if total_monthly_mortgage else None,
            total_monthly_cash_flow=round(total_monthly_cash_flow, 2) if total_monthly_cash_flow else None,
            total_monthly_cash_flow_formatted=(
                f"${total_monthly_cash_flow:,.0f}" if total_monthly_cash_flow else None
            ),
            avg_risk_score=round(avg_risk, 1) if avg_risk else None,
            risk_label=_risk_label(round(avg_risk) if avg_risk else None),
            by_property_type=by_type,
            by_city=by_city,
        )

    # ── Private Helpers ────────────────────────────────────────────────────────

    async def _get_entry(self, session_token: str, entry_id: int) -> Optional[PortfolioEntry]:
        result = await self.db.execute(
            select(PortfolioEntry).where(
                PortfolioEntry.id == entry_id,
                PortfolioEntry.session_token == session_token,
            )
        )
        return result.scalar_one_or_none()

    async def _get_property(self, property_id: int) -> Optional[Property]:
        result = await self.db.execute(
            select(Property).where(Property.id == property_id)
        )
        return result.scalar_one_or_none()

    def _build_entry_response(
        self,
        entry: PortfolioEntry,
        prop: Optional[Property],
    ) -> Dict[str, Any]:
        """Build a rich entry dict with computed financial metrics."""
        purchase_price = entry.purchase_price or (prop.list_price if prop else None)
        monthly_income = entry.actual_monthly_rent or (prop.monthly_rent_estimate if prop else None)

        # Mortgage calculation
        monthly_mortgage: Optional[float] = None
        equity: Optional[float] = None

        if purchase_price and entry.down_payment_pct is not None:
            down = purchase_price * entry.down_payment_pct
            loan = purchase_price - down
            equity = down  # Simplified: equity ≈ down payment (no amortisation table)

            if entry.mortgage_rate and entry.loan_term_years:
                monthly_rate = entry.mortgage_rate / 12
                n_payments = entry.loan_term_years * 12
                if monthly_rate > 0:
                    monthly_mortgage = loan * (
                        monthly_rate * (1 + monthly_rate) ** n_payments
                    ) / ((1 + monthly_rate) ** n_payments - 1)
                else:
                    monthly_mortgage = loan / n_payments

        # Annual operating costs estimate (35% of gross rent)
        annual_income = (monthly_income or 0) * 12
        operating_costs = annual_income * 0.35
        noi = annual_income - operating_costs

        # Cash flow & returns
        monthly_cash_flow: Optional[float] = None
        if monthly_income is not None:
            monthly_cash_flow = monthly_income - (monthly_mortgage or 0) - (operating_costs / 12)

        cash_on_cash: Optional[float] = None
        if equity and equity > 0 and noi:
            cash_on_cash = noi / equity

        return {
            "id": entry.id,
            "property_id": entry.property_id,
            "session_token": entry.session_token,
            "purchase_price": purchase_price,
            "purchase_date": entry.purchase_date,
            "down_payment_pct": entry.down_payment_pct,
            "mortgage_rate": entry.mortgage_rate,
            "loan_term_years": entry.loan_term_years,
            "actual_monthly_rent": entry.actual_monthly_rent,
            "notes": entry.notes,
            "status": entry.status,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            # Computed
            "equity_estimate": round(equity) if equity else None,
            "equity_formatted": f"${equity:,.0f}" if equity else None,
            "monthly_mortgage_payment": round(monthly_mortgage, 2) if monthly_mortgage else None,
            "monthly_income": round(monthly_income, 2) if monthly_income else None,
            "monthly_cash_flow": round(monthly_cash_flow, 2) if monthly_cash_flow else None,
            "monthly_cash_flow_formatted": f"${monthly_cash_flow:,.0f}" if monthly_cash_flow else None,
            "cash_on_cash_return": round(cash_on_cash, 4) if cash_on_cash else None,
            "cash_on_cash_pct": f"{cash_on_cash * 100:.1f}%" if cash_on_cash else None,
            # Property shortcut fields (for summary aggregation)
            "cap_rate": prop.cap_rate if prop else None,
            "risk_score": prop.risk_score if prop else None,
            "property_type": prop.property_type if prop else None,
            "city": prop.city if prop else None,
            # Embedded property
            "property": PropertyResponse.from_orm_with_metrics(prop) if prop else None,
        }


def _risk_label(score: Optional[int]) -> Optional[str]:
    if score is None:
        return None
    if score <= 30:
        return "Low Risk"
    if score <= 65:
        return "Medium Risk"
    return "High Risk"
