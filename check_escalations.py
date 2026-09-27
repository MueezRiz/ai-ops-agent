from db import get_connection

def check_escalations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, issue, status, created_at FROM tickets WHERE status = 'needs_review' ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No escalated tickets found.")
        return

    print(f"Found {len(rows)} escalated ticket(s):\n")
    for row in rows:
        print(f"  ID:         {row[0]}")
        print(f"  Issue:      {row[1]}")
        print(f"  Status:     {row[2]}")
        print(f"  Created at: {row[3]}")
        print()

if __name__ == "__main__":
    check_escalations()
