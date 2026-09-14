import os
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

import engine

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EquiTrade Guardian - Ikeja Cooperative</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-canvas: #09090b;
      --bg-card: #121215;
      --border-color: #27272a;
      --text-primary: #ffffff;
      --text-muted: #a1a1aa;
      --accent-green: #22c55e;
      --danger-red: #ef4444;
      --warn-yellow: #eab308;
      --font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }
    body {
      margin: 0;
      font-family: var(--font-sans);
      background: var(--bg-canvas);
      color: var(--text-primary);
      line-height: 1.5;
      background-image: radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px);
      background-size: 20px 20px;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 7rem 2rem 3rem; /* padding top for floating header */
    }
    /* Floating Header */
    header {
      position: fixed;
      top: 1.5rem;
      left: 50%;
      transform: translateX(-50%);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      background: rgba(18, 18, 21, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      padding: 0.75rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 3rem;
      z-index: 100;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      width: max-content;
      max-width: 90%;
    }
    .brand-name {
      font-weight: 800;
      font-size: 1.1rem;
      letter-spacing: -0.03em;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: var(--text-primary);
    }
    .brand-name span.mono {
      font-family: var(--font-mono);
      color: var(--text-muted);
      font-weight: 500;
      font-size: 0.85rem;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    /* Cards */
    .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card h2 {
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0 0 1.25rem 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 0.75rem;
    }
    
    /* Status Strip */
    .status-strip {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .stat-title {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    .stat-value {
      font-size: 2.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    
    /* Status Badges */
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      border: 1px solid rgba(34, 197, 94, 0.2);
      background: rgba(34, 197, 94, 0.05);
      border-radius: 9999px;
      padding: 0.25rem 0.625rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--accent-green);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .status-pill .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--accent-green);
      box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
    }
    .status-pill.needs_review, .status-pill.unprocessed {
      border-color: rgba(234, 179, 8, 0.2);
      background: rgba(234, 179, 8, 0.05);
      color: var(--warn-yellow);
    }
    .status-pill.needs_review .dot, .status-pill.unprocessed .dot { 
      background-color: var(--warn-yellow); 
      box-shadow: 0 0 8px rgba(234, 179, 8, 0.6); 
    }
    
    .status-pill.skipped {
      border-color: rgba(161, 161, 170, 0.2);
      background: rgba(161, 161, 170, 0.05);
      color: var(--text-muted);
    }
    .status-pill.skipped .dot { background-color: var(--text-muted); box-shadow: none; }
    
    /* Buttons */
    button, .btn {
      background-color: #ffffff;
      color: #09090b;
      font-family: var(--font-mono);
      padding: 0.625rem 1.25rem;
      border-radius: 8px;
      border: none;
      font-weight: 600;
      font-size: 0.875rem;
      cursor: pointer;
      transition: transform 0.2s ease, opacity 0.2s ease;
      white-space: nowrap;
    }
    button:hover { transform: translateY(-1px); opacity: 0.9; }
    button.secondary {
      background-color: transparent;
      border: 1px solid var(--border-color);
      color: #f4f4f5;
    }
    button.secondary:hover {
      background-color: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.2);
    }
    button.nav-btn {
      padding: 0.4rem 1rem;
      font-size: 0.8rem;
    }
    
    /* Queue Item */
    .queue-item {
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1rem;
      background: rgba(255, 255, 255, 0.02);
      transition: border-color 0.2s;
    }
    .queue-item:hover {
      border-color: rgba(255, 255, 255, 0.15);
    }
    .queue-item.unprocessed {
      border-left: 4px solid var(--border-color);
    }
    .queue-item.needs_review {
      border-left: 4px solid var(--warn-yellow);
    }
    
    .queue-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 0.75rem;
    }
    .debtor-name {
      font-size: 1.15rem;
      font-weight: 700;
    }
    .payment-amt {
      font-family: var(--font-mono);
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    .payment-ref {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.05);
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      letter-spacing: 0.05em;
    }
    
    .flag-reason {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--warn-yellow);
      margin: 1rem 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(234, 179, 8, 0.05);
      border: 1px solid rgba(234, 179, 8, 0.2);
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
    }
    
    .queue-action {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      margin-top: 1rem;
    }
    
    select {
      background: #09090b;
      color: #f4f4f5;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 0.6rem 1rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      flex: 1;
      outline: none;
    }
    select:focus { border-color: rgba(255, 255, 255, 0.3); }
    
    /* Ledger Table */
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { text-align: left; padding: 1rem 0.5rem; border-bottom: 1px solid var(--border-color); }
    th { 
      font-family: var(--font-mono);
      color: var(--text-muted); 
      font-size: 0.75rem; 
      text-transform: uppercase; 
      letter-spacing: 0.1em;
    }
    td.mono-cell { font-family: var(--font-mono); font-size: 0.85rem; }
    
    .flash {
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid rgba(34, 197, 94, 0.2);
      color: var(--accent-green);
      font-family: var(--font-mono);
      padding: 1rem 1.5rem;
      border-radius: 8px;
      margin-bottom: 2rem;
      font-size: 0.875rem;
    }
    
    /* Meter Panel */
    .meter-widget {
      text-align: center;
    }
    .meter-balance {
      font-size: 3rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin: 1rem 0 0.5rem;
    }
    .meter-balance.low { color: var(--danger-red); }
    .meter-details {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--text-muted);
      line-height: 1.8;
      margin-bottom: 1.5rem;
    }
    .last-token {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1.5rem;
      text-align: left;
    }
    .last-token-title {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 0.5rem;
    }
    .last-token-value {
      font-family: var(--font-mono);
      font-size: 1.25rem;
      color: var(--accent-green);
      font-weight: 600;
      letter-spacing: 0.1em;
      display: block;
      margin-bottom: 0.25rem;
    }
    .meter-actions {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    
    .top-action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      padding: 1.5rem;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
    }
    
    .footer-note {
      text-align: center;
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.75rem;
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
    }
  </style>
</head>
<body>
  <header>
    <div class="brand-name">
      EquiTrade Guardian <span class="mono">// Ikeja Coop</span>
    </div>
    <div class="header-actions">
      <form method="post" action="{{ url_for('reset') }}" style="margin: 0;">
        <button class="secondary nav-btn" type="submit">Reset Demo</button>
      </form>
    </div>
  </header>

  <div class="container">
    {% if flash %}<div class="flash">> {{ flash }}</div>{% endif %}

    <div class="status-strip">
      {% set needs_review_count = payments | selectattr('status', 'equalto', 'needs_review') | list | length %}
      {% set open_dues_count = open_invoices | length %}
      
      <div class="stat-card">
        <span class="stat-title">Open Dues</span>
        <span class="stat-value">{{ open_dues_count }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-title">Review Queue</span>
        <span class="stat-value" {% if needs_review_count > 0 %}style="color: var(--warn-yellow)"{% endif %}>{{ needs_review_count }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-title">Meter Health</span>
        <span class="stat-value" {% if meter.balance <= meter.low_balance_threshold %}style="color: var(--danger-red)"{% endif %}>
          {% if meter.balance <= meter.low_balance_threshold %}LOW{% else %}OK{% endif %}
        </span>
      </div>
    </div>

    <div class="top-action-bar">
      <div>
        <strong style="font-size: 1.15rem; font-weight: 700;">Payment Matching Engine</strong>
        <p style="margin: 0.25rem 0 0; font-size: 0.95rem; color: var(--text-muted);">Process NIBSS transfers and auto-match precise payments. The agent stops when unsure.</p>
      </div>
      <form method="post" action="{{ url_for('match') }}" style="margin: 0;">
        <button type="submit">Run Auto-Match</button>
      </form>
    </div>

    <div class="grid">
      <div class="main-col">
        <section class="card">
          <h2>Attention Queue</h2>
          {% set queue_payments = payments | rejectattr('status', 'in', ['reconciled', 'skipped']) | list %}
          {% if queue_payments %}
            {% for p in queue_payments %}
            {% set iso = p.iso20022 %}
            <div class="queue-item {{ p.status }}">
              <div class="queue-header">
                <span class="debtor-name">{{ iso.debtor_name }}</span>
                <span class="payment-amt">₦{{ "{:,.2f}".format(iso.amount_ngn) }}</span>
              </div>
              <div style="margin-bottom: 1rem; display: flex; align-items: center; gap: 1rem;">
                <span class="payment-ref">{{ iso.end_to_end_id or "Missing Reference" }}</span>
                <span class="status-pill {{ p.status }}">
                  <span class="dot"></span>
                  {{ p.status|replace('_', ' ') }}
                </span>
              </div>
              
              {% if p.flag_reason %}
              <div class="flag-reason">
                <strong>[HOLD]</strong> {{ p.flag_reason }}
              </div>
              {% endif %}
              
              {% if p.status == "needs_review" %}
              <form class="queue-action" method="post" action="{{ url_for('resolve') }}">
                <input type="hidden" name="payment_id" value="{{ p.id }}">
                <select name="invoice_id">
                  <option value="">-- Skip / No Match --</option>
                  {% for inv in open_invoices %}
                  <option value="{{ inv.id }}">{{ inv.member_name }} (₦{{ "{:,.2f}".format(inv.amount_due) }}) - {{ inv.reference }}</option>
                  {% endfor %}
                </select>
                <button type="submit">Confirm Match</button>
              </form>
              {% endif %}
            </div>
            {% endfor %}
          {% else %}
            <p style="color: var(--text-muted); text-align: center; padding: 2rem 0; font-family: var(--font-mono); font-size: 0.85rem;">No payments require manual attention.</p>
          {% endif %}
        </section>

        <section class="card">
          <h2>Settled Ledger</h2>
          {% set settled_payments = payments | selectattr('status', 'in', ['reconciled', 'skipped']) | list %}
          {% if settled_payments %}
          <table>
            <tr><th>Debtor</th><th>Amount</th><th>Ref</th><th>Matched To</th><th>Status</th></tr>
            {% for p in settled_payments %}
            {% set iso = p.iso20022 %}
            <tr>
              <td>{{ iso.debtor_name }}</td>
              <td class="mono-cell" style="color: var(--text-primary);">₦{{ "{:,.2f}".format(iso.amount_ngn) }}</td>
              <td class="mono-cell">{{ iso.end_to_end_id or "—" }}</td>
              <td class="mono-cell">{{ p.matched_invoice or "—" }}</td>
              <td>
                <span class="status-pill {{ p.status }}">
                  <span class="dot"></span>
                  {{ p.status }}
                </span>
              </td>
            </tr>
            {% endfor %}
          </table>
          {% else %}
            <p style="color: var(--text-muted); font-size: 0.95rem;">No reconciled payments yet.</p>
          {% endif %}
        </section>
      </div>

      <div class="side-col">
        <section class="card meter-widget">
          <h2>Prepaid Meter</h2>
          <div class="meter-balance {% if meter.balance <= meter.low_balance_threshold %}low{% endif %}">
            ₦{{ "{:,.2f}".format(meter.balance) }}
          </div>
          <div class="meter-details">
            <strong>{{ meter.disco }}</strong> // METER {{ meter.meter_number }}<br>
            THRESHOLD: ₦{{ "{:,.2f}".format(meter.low_balance_threshold) }}<br>
            AUTO-APPROVE: ≤ ₦{{ "{:,.2f}".format(meter.auto_approve_limit) }}
          </div>
          
          {% if meter.last_vend %}
          <div class="last-token">
            <div class="last-token-title">Last Token</div>
            <span class="last-token-value">{{ meter.last_vend.token }}</span>
            <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">
              {{ meter.last_vend.units_kwh }} kWh // APP BY: {{ meter.last_vend.approved_by }}
            </div>
          </div>
          {% endif %}

          <div class="meter-actions">
            <form method="post" action="{{ url_for('meter') }}" style="margin: 0;">
              <input type="hidden" name="decision" value="yes">
              <button type="submit" style="width: 100%;">Approve ₦{{ "{:,.2f}".format(meter.recommended_topup) }}</button>
            </form>
            <form method="post" action="{{ url_for('meter') }}" style="margin: 0;">
              <input type="hidden" name="decision" value="no">
              <button class="secondary" type="submit" style="width: 100%;">Deny Top-Up</button>
            </form>
          </div>
        </section>

        <section class="card">
          <h2>Open Invoices</h2>
          {% if open_invoices %}
          <table style="font-size: 0.9rem;">
            <tr><th>Member</th><th>Amount</th><th>Ref</th></tr>
            {% for inv in open_invoices %}
            <tr>
              <td>{{ inv.member_name }}</td>
              <td class="mono-cell" style="color: var(--text-primary);">₦{{ "{:,.0f}".format(inv.amount_due) }}</td>
              <td class="mono-cell">{{ inv.reference }}</td>
            </tr>
            {% endfor %}
          </table>
          {% else %}
            <p style="color: var(--text-muted); font-size: 0.95rem;">All dues are settled.</p>
          {% endif %}
        </section>
      </div>
    </div>
    
    <div class="footer-note">
      > TERMINAL AGENT (STRANDS + OLLAMA) // python agent.py // python reset_data.py
    </div>
  </div>
</body>
</html>
"""


def _flash_redirect(message: str):
    return redirect(url_for("home", flash=message))


@app.route("/")
def home():
    snap = engine.snapshot()
    return render_template_string(
        PAGE,
        invoices=snap["invoices"],
        payments=snap["payments"],
        meter=snap["meter"],
        open_invoices=engine.list_open_invoices(),
        flash=request.args.get("flash"),
    )


@app.post("/match")
def match():
    result = engine.apply_matching_rules()
    auto = len(result["auto_reconciled"])
    flagged = len(result["needs_review"])
    return _flash_redirect(
        f"Matching done: {auto} auto-reconciled, {flagged} sent to a human."
    )


@app.post("/resolve")
def resolve():
    message = engine.apply_human_decision(
        request.form["payment_id"],
        request.form.get("invoice_id") or None,
    )
    return _flash_redirect(message)


@app.post("/meter")
def meter():
    decision = request.form.get("decision", "no")
    meter_state = engine.check_meter()
    if meter_state["balance"] >= meter_state["low_balance_threshold"]:
        return _flash_redirect("Meter is already above the low-balance threshold.")
    if meter_state["recommended_topup"] > meter_state["auto_approve_limit"]:
        if decision not in ("yes", "y"):
            return _flash_redirect("Human denied the top-up. No purchase was made.")
        approved_by = "human"
    else:
        approved_by = "policy:auto_approve_limit"
    receipt = engine.buy_electricity_credit(
        meter_state["recommended_topup"], approved_by=approved_by
    )
    return _flash_redirect(
        f"VendPower token {receipt['token']} · {receipt['units_kwh']} kWh."
    )


@app.post("/reset")
def reset():
    engine.reset_data()
    return _flash_redirect("Demo data restored.")


@app.get("/api/snapshot")
def api_snapshot():
    return jsonify(engine.snapshot())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
