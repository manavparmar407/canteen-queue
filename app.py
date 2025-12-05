from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
)
from db_config import get_connection
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "canteen123"  # for session
app.permanent_session_lifetime = timedelta(minutes=30)

# ------------------------------------------------------
# HOME = Student Dashboard
# ------------------------------------------------------
@app.route("/")
def student_home():
    return render_template("index.html")


# ------------------------------------------------------
# API: MENU
# ------------------------------------------------------
@app.route("/menu", methods=["GET"])
def get_menu():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT item_id, item_name, category, price, avg_prep_time_minutes
        FROM menu_items
        WHERE is_active = TRUE
        """
    )
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(data)


# ------------------------------------------------------
# API: PLACE ORDER (Student)
# ------------------------------------------------------
@app.route("/order", methods=["POST"])
def place_order():
    try:
        data = request.json

        name = data.get("name")
        reg_id = data.get("reg_id")
        item_id = data.get("item_id")
        quantity = data.get("quantity", 1)

        if not all([name, reg_id, item_id]):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if student exists
        cursor.execute(
            "SELECT student_id FROM students WHERE reg_id = %s", (reg_id,)
        )
        student = cursor.fetchone()

        if student:
            student_id = student["student_id"]
        else:
            cursor.execute(
                "INSERT INTO students (name, reg_id) VALUES (%s, %s)",
                (name, reg_id),
            )
            conn.commit()
            student_id = cursor.lastrowid

        # Insert the order
        cursor.execute(
            """
            INSERT INTO orders (student_id, item_id, quantity, status)
            VALUES (%s, %s, %s, 'PENDING')
            """,
            (student_id, item_id, quantity),
        )
        conn.commit()
        order_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify(
            {"message": "Order placed successfully", "order_id": order_id}
        )

    except Exception as e:
        print("Error in place_order:", e)
        return jsonify({"error": "Server error while placing order"}), 500


# ------------------------------------------------------
# API: CURRENT QUEUE STATUS
# ------------------------------------------------------
@app.route("/queue-status", methods=["GET"])
def queue_status():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Only count PENDING orders
    cursor.execute("""
        SELECT COUNT(*) AS pending_orders
        FROM orders
        WHERE status = 'PENDING'
        AND DATE(order_time) = CURDATE()
    """)
    pending_row = cursor.fetchone()
    pending = pending_row["pending_orders"]

    # Calculate wait time (based on pending orders)
    cursor.execute("""
        SELECT SUM(m.avg_prep_time_minutes * o.quantity) AS total_wait
        FROM orders o
        JOIN menu_items m ON o.item_id = m.item_id
        WHERE o.status = 'PENDING'
        AND DATE(order_time) = CURDATE()
    """)
    wait_row = cursor.fetchone()

    total_wait = wait_row["total_wait"] or 0
    avg_wait = total_wait / pending if pending > 0 else 0

    cursor.close()
    conn.close()

    return jsonify({
        "pending_orders": pending,
        "avg_wait_time": round(avg_wait, 2)
    })



# ------------------------------------------------------
# API: TODAY'S SUMMARY
# ------------------------------------------------------
@app.route("/stats/today", methods=["GET"])
def stats_today():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM v_daily_order_summary
        WHERE order_date = CURDATE()
        """
    )
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(row or {"message": "No orders placed today"})


# ------------------------------------------------------
# ADMIN LOGIN / LOGOUT
# ------------------------------------------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # simple hardcoded admin
        if username == "admin" and password == "1234":
            session["admin"] = True
            session.permanent = True
            return redirect(url_for("kitchen_page"))
        else:
            return render_template(
                "admin_login.html", error="Invalid username or password"
            )

    # GET
    return render_template("admin_login.html")


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ------------------------------------------------------
# KITCHEN DASHBOARD (ADMIN SIDE)
# ------------------------------------------------------
@app.route("/kitchen")
def kitchen_page():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("kitchen.html")


# Fetch pending + preparing + ready orders
@app.route("/kitchen/orders")
def kitchen_orders():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT o.order_id,
               s.name AS student_name,
               s.reg_id,
               m.item_name,
               o.quantity,
               o.status,
               o.order_time
        FROM orders o
        JOIN students s ON o.student_id = s.student_id
        JOIN menu_items m ON o.item_id = m.item_id
        WHERE o.status IN ('PENDING', 'PREPARING', 'READY')
        ORDER BY o.order_time ASC
        """
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


# Update order status
@app.route("/kitchen/update", methods=["POST"])
def update_order_status():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    order_id = data.get("order_id")
    status = data.get("status")

    if not order_id or status not in (
        "PENDING",
        "PREPARING",
        "READY",
        "DELIVERED",
        "CANCELLED",
    ):
        return jsonify({"error": "Invalid data"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    if status in ("READY", "DELIVERED"):
        cursor.execute(
            """
            UPDATE orders
            SET status = %s,
                actual_ready_time = IF(actual_ready_time IS NULL, NOW(), actual_ready_time)
            WHERE order_id = %s
            """,
            (status, order_id),
        )
    else:
        cursor.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s",
            (status, order_id),
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Status updated"})


if __name__ == "__main__":
    app.run(debug=True)
