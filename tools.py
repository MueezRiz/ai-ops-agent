from models import (
    OrderStatusInput, OrderStatusOutput,
    CreateTicketInput, CreateTicketOutput,
    EscalateInput, EscalateOutput
)

def check_order_status(order_id: str) -> dict:
    input_data = OrderStatusInput(order_id=order_id)
    result = OrderStatusOutput(
        order_id=input_data.order_id,
        status="in transit",
        estimated_delivery="2024-01-18",
        carrier="UPS"
    )
    return result.dict()

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