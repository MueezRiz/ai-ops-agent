from pydantic import BaseModel

# --- check_order_status ---
class OrderStatusInput(BaseModel):
    order_id: str

class OrderStatusOutput(BaseModel):
    order_id: str
    status: str
    estimated_delivery: str
    carrier: str

# --- create_ticket ---
class CreateTicketInput(BaseModel):
    issue: str

class CreateTicketOutput(BaseModel):
    ticket_id: str
    status: str
    issue: str
    created_at: str

# --- escalate_to_human ---
class EscalateInput(BaseModel):
    reason: str

class EscalateOutput(BaseModel):
    escalated: bool
    reason: str
    assigned_to: str
    estimated_response: str