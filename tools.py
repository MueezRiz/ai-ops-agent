def check_order_status(order_id: str) -> dict:
    # Mock data — hardcoded fake orders
    mock_orders = {
        "123": {"status": "shipped", "eta": "2 days"},
        "456": {"status": "processing", "eta": "5 days"},
        "789": {"status": "delivered", "eta": "already delivered"},
    }
    
    order = mock_orders.get(order_id)
    if order:
        return {"order_id": order_id, "status": order["status"], "eta": order["eta"]}
    else:
        return {"order_id": order_id, "status": "not found", "eta": None}