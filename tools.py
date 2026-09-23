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
    return result.dict()

def escalate_to_human(reason: str) -> dict:
    input_data = EscalateInput(reason=reason)
    result = EscalateOutput(
        escalated=True,
        reason=input_data.reason,
        assigned_to="support team",
        estimated_response="within 2 hours"
    )
    return result.dict()