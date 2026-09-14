# SIMULATED DATA ONLY — models NIBSS-style ISO 20022 payments and IKEDC-style prepaid meter; does not connect to any real NIBSS, IKEDC, or VendPower API.
"""Deterministic matching and meter policy.

The model orchestrates; these functions decide. Ambiguous payments are never
auto-matched, and large electricity top-ups never go through without approval.
"""

from __future__ import annotations

import json
import os
import random
import shutil
from typing import Callable

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def _save(filename: str, data) -> None:
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def reset_data() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in ("invoices.json", "payments.json", "meter.json"):
        shutil.copyfile(
            os.path.join(FIXTURES_DIR, name),
            os.path.join(DATA_DIR, name),
        )


def _norm_name(name: str) -> str:
    return " ".join((name or "").lower().replace(".", " ").split())


def _names_compatible(payer: str, member: str) -> bool:
    p = _norm_name(payer)
    m = _norm_name(member)
    if not p or not m:
        return False
    if p == m:
        return True
    p_parts = [x for x in p.split() if len(x) > 1]
    m_parts = m.split()
    if p_parts and all(part in m for part in p_parts):
        return True
    if p_parts and m_parts and p_parts[-1] == m_parts[-1]:
        return True
    return False


def apply_matching_rules() -> dict:
    """Match unprocessed payments using conservative ISO 20022-style rules.

    Auto-reconcile only when EndToEndId / reference uniquely matches an open
    invoice AND the amount is exact AND the debtor name is compatible.
    Everything else is queued for a human. Never guess.
    """
    invoices = _load("invoices.json")
    payments = _load("payments.json")
    open_invoices = [i for i in invoices if i["status"] == "open"]

    auto = []
    flagged = []

    for payment in payments:
        if payment.get("status") != "unprocessed":
            continue

        iso = payment.get("iso20022", {})
        ref = (iso.get("end_to_end_id") or payment.get("reference") or "").strip()
        amount = iso.get("amount_ngn", payment.get("amount"))
        payer = iso.get("debtor_name") or payment.get("payer_name") or ""

        reason = None
        match = None

        if not ref:
            reason = (
                "Missing EndToEndId / payment reference. "
                "Name-only matching is not allowed."
            )
        else:
            ref_hits = [i for i in open_invoices if i["reference"] == ref]
            if len(ref_hits) == 0:
                reason = f"No open invoice has reference {ref}."
            elif len(ref_hits) > 1:
                reason = f"Reference {ref} matches more than one open invoice."
            else:
                candidate = ref_hits[0]
                if candidate["amount_due"] != amount:
                    reason = (
                        f"Reference matches {candidate['id']} but amount differs "
                        f"(paid {amount} NGN, due {candidate['amount_due']} NGN)."
                    )
                elif not _names_compatible(payer, candidate["member_name"]):
                    reason = (
                        f"Reference matches {candidate['id']} but debtor name "
                        f"'{payer}' does not match member '{candidate['member_name']}'."
                    )
                else:
                    match = candidate

        if match:
            payment["status"] = "reconciled"
            payment["matched_invoice"] = match["id"]
            payment["processed"] = True
            payment["flag_reason"] = None
            match["status"] = "paid"
            match["paid_by_payment"] = payment["id"]
            open_invoices = [i for i in open_invoices if i["id"] != match["id"]]
            auto.append(
                {
                    "payment_id": payment["id"],
                    "invoice_id": match["id"],
                    "member": match["member_name"],
                    "amount": amount,
                    "rule": "exact EndToEndId + exact amount + compatible name",
                }
            )
        else:
            payment["status"] = "needs_review"
            payment["flag_reason"] = reason
            payment["processed"] = False
            flagged.append(
                {
                    "payment_id": payment["id"],
                    "payer": payer,
                    "amount": amount,
                    "reference": ref or None,
                    "reason": reason,
                }
            )

    _save("payments.json", payments)
    _save("invoices.json", invoices)
    return {"auto_reconciled": auto, "needs_review": flagged}


def list_open_invoices() -> list:
    invoices = _load("invoices.json")
    return [i for i in invoices if i["status"] == "open"]


def list_needs_review() -> list:
    payments = _load("payments.json")
    return [p for p in payments if p.get("status") == "needs_review"]


def apply_human_decision(payment_id: str, invoice_id: str | None) -> str:
    payments = _load("payments.json")
    invoices = _load("invoices.json")
    payment = next((p for p in payments if p["id"] == payment_id), None)
    if not payment:
        return f"Unknown payment {payment_id}."

    if not invoice_id:
        payment["status"] = "skipped"
        payment["processed"] = True
        _save("payments.json", payments)
        return f"Human skipped {payment_id}; left unmatched."

    invoice = next((i for i in invoices if i["id"] == invoice_id), None)
    if not invoice:
        return f"Unknown invoice {invoice_id}."
    if invoice["status"] != "open":
        return f"Invoice {invoice_id} is not open."

    payment["status"] = "reconciled"
    payment["matched_invoice"] = invoice_id
    payment["processed"] = True
    payment["human_override"] = True
    invoice["status"] = "paid"
    invoice["paid_by_payment"] = payment_id
    _save("payments.json", payments)
    _save("invoices.json", invoices)
    return f"Human matched {payment_id} to {invoice_id} ({invoice['member_name']})."


def review_flagged_with_human(ask: Callable[[str], str] | None = None) -> list[str]:
    ask = ask or input
    results = []
    flagged = list_needs_review()
    if not flagged:
        return ["No payments waiting for human review."]

    open_inv = list_open_invoices()
    for payment in flagged:
        iso = payment.get("iso20022", {})
        print("\n" + "=" * 60)
        print(f"HUMAN REVIEW NEEDED — {payment['id']}")
        print(f"Debtor:     {iso.get('debtor_name', payment.get('payer_name'))}")
        print(f"Amount:     {iso.get('amount_ngn', payment.get('amount'))} NGN")
        print(f"EndToEndId: {iso.get('end_to_end_id') or '(missing)'}")
        print(f"Reason:     {payment.get('flag_reason')}")
        print("Open invoices:")
        for inv in open_inv:
            print(
                f"  {inv['id']}: {inv['member_name']}  "
                f"{inv['amount_due']} NGN  ref={inv['reference']}"
            )
        print("=" * 60)
        try:
            decision = ask(
                "Type an invoice ID to match, or press Enter to skip: "
            ).strip()
        except EOFError:
            decision = ""
        message = apply_human_decision(payment["id"], decision or None)
        print(message)
        results.append(message)
        open_inv = list_open_invoices()
    return results


def check_meter() -> dict:
    return _load("meter.json")


def _generate_token() -> str:
    parts = [f"{random.randint(0, 9999):04d}" for _ in range(5)]
    return "-".join(parts)


def buy_electricity_credit(amount: float, approved_by: str) -> dict:
    meter = _load("meter.json")
    token = _generate_token()
    units = round(amount / float(meter.get("tariff_ngn_per_kwh", 80)), 2)
    meter["balance"] = round(meter["balance"] + amount, 2)
    meter["last_topup"] = amount
    meter["last_token"] = token
    meter["last_approved_by"] = approved_by
    receipt = {
        "provider": "VendPower (simulated)",
        "disco": meter.get("disco"),
        "meter_number": meter.get("meter_number"),
        "amount_ngn": amount,
        "token": token,
        "units_kwh": units,
        "new_balance_ngn": meter["balance"],
        "approved_by": approved_by,
        "status": "success",
    }
    meter["last_vend"] = receipt
    _save("meter.json", meter)
    return receipt


def handle_meter_with_human(ask: Callable[[str], str] | None = None) -> dict:
    ask = ask or input
    meter = check_meter()
    if meter["balance"] >= meter["low_balance_threshold"]:
        return {
            "action": "none",
            "reason": (
                f"Balance {meter['balance']} NGN is at or above the "
                f"{meter['low_balance_threshold']} NGN threshold."
            ),
            "meter": meter,
        }

    amount = meter["recommended_topup"]
    approved_by = "policy:auto_approve_limit"

    if amount > meter["auto_approve_limit"]:
        print("\n" + "=" * 60)
        print(f"APPROVAL NEEDED — electricity top-up of {amount} NGN")
        print(f"Meter:    {meter.get('meter_number')} ({meter.get('disco')})")
        print(f"Balance:  {meter['balance']} NGN")
        print(f"Limit:    auto-approve up to {meter['auto_approve_limit']} NGN")
        print("=" * 60)
        try:
            decision = ask("Approve this top-up? (yes/no): ").strip().lower()
        except EOFError:
            decision = "no"
        if decision not in ("yes", "y"):
            return {
                "action": "denied",
                "reason": "Human denied the top-up. No purchase was made.",
                "meter": check_meter(),
            }
        approved_by = "human"

    receipt = buy_electricity_credit(amount, approved_by=approved_by)
    return {"action": "purchased", "receipt": receipt, "meter": check_meter()}


def snapshot() -> dict:
    return {
        "invoices": _load("invoices.json"),
        "payments": _load("payments.json"),
        "meter": _load("meter.json"),
    }
