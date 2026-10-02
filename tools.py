import uuid
from db import get_connection


from models import (
    OrderStatusInput, OrderStatusOutput,
    CreateTicketInput, CreateTicketOutput,
    EscalateInput, EscalateOutput
)

def check_order_status(order_id: str) -> dict:
    return {
        "order_id": order_id,
        "status": "delayed",
        "reason": "weather disruption",
        "carrier": "UPS",
        "estimated_delivery": "January 25, 2024"
    }

def create_ticket(issue: str) -> dict:
    input_data = CreateTicketInput(issue=issue)
    result = CreateTicketOutput(
        ticket_id="T-456",
        status="created",
        issue=input_data.issue,
        created_at="2024-01-15T10:30:00Z"
    )
    return result.model_dump()


def escalate_to_human(reason: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (id, issue, status, created_at) VALUES (%s, %s, %s, NOW())",
        (str(uuid.uuid4()), reason, "needs_review")
    )
    conn.commit()
    cur.close()
    conn.close()
    return f"Escalated to human review. Reason: {reason}"