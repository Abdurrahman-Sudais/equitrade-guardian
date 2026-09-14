from strands import Agent
from strands.models.ollama import OllamaModel

from tools import apply_matching_rules, handle_prepaid_meter, review_flagged_payments

SYSTEM_PROMPT = """You are the daily operations agent for Ikeja Community Cooperative,
a small Nigerian nonprofit. You do not invent matches or spend money on your own.

Each run, call exactly one tool at a time, wait for the result, then call the next, in this order:
1. apply_matching_rules
2. review_flagged_payments
3. handle_prepaid_meter

Then write a short summary from the tool results: what was auto-reconciled,
what a human decided, and what happened with the meter (including any token).

Never write fake JSON tool calls. Never skip a tool. Never guess a payment match.
Policy lives in the tools — you only orchestrate and explain.
"""

model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen2.5:7b",
    temperature=0.0,
    max_tokens=800,
)

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        apply_matching_rules,
        review_flagged_payments,
        handle_prepaid_meter,
    ],
)

if __name__ == "__main__":
    print("EquiTrade Guardian — daily reconciliation run\n")
    try:
        result = agent(
            "Run today's reconciliation for Ikeja Community Cooperative, "
            "then handle the prepaid meter."
        )
        print("\n--- FINAL SUMMARY ---")
        print(result)
    except Exception as exc:
        msg = str(exc).lower()
        if any(kw in msg for kw in ("connect", "connection", "refused", "timeout", "ollama")):
            print(
                "\nERROR: Could not connect to Ollama at http://localhost:11434"
                "\nMake sure Ollama is running and qwen2.5:7b is pulled:"
                "\n  ollama serve          # start the local server"
                "\n  ollama pull qwen2.5:7b  # download the model"
            )
        else:
            raise
