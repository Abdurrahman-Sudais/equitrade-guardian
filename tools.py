import json

from strands import tool

import engine


@tool
def apply_matching_rules() -> str:
    """Run conservative payment-to-invoice matching on all unprocessed payments.

    Auto-reconciles only when ISO 20022 EndToEndId matches an open invoice
    reference, the amount is exact, and the debtor name is compatible.
    Ambiguous cases are queued for human review — this tool never guesses.
    Call this first.
    """
    result = engine.apply_matching_rules()
    return json.dumps(result, indent=2)


@tool
def review_flagged_payments() -> str:
    """Pause and ask a human to resolve each payment that matching could not
    confidently auto-reconcile. Call this after apply_matching_rules.
    """
    results = engine.review_flagged_with_human()
    return json.dumps(results, indent=2)


@tool
def handle_prepaid_meter() -> str:
    """Check the prepaid electricity meter and top it up if needed.

    Small top-ups at or below the auto-approve limit are purchased
    immediately via the simulated VendPower API. Larger top-ups pause
    for a human yes/no. Call this after payments have been handled.
    """
    result = engine.handle_meter_with_human()
    return json.dumps(result, indent=2)
