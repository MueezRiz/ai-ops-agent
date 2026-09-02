
def check_order_status(order_id: str) -> dict:
    return {
        "order_id": order_id,
        "status": "in transit",
        "estimated_delivery": "2024-01-18",
        "carrier": "UPS"
    }

def create_ticket(issue: str) -> dict:
    return {
        "ticket_id": "T-456",
        "status": "created",
        "issue": issue,
        "created_at": "2024-01-15T10:30:00Z"
    }

def escalate_to_human(reason: str) -> dict:
    return {
        "escalated": True,
        "reason": reason,
        "assigned_to": "support team",
        "estimated_response": "within 2 hours"
    }
