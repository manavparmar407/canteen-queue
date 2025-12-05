async function loadKitchenOrders() {
    const res = await fetch('/kitchen/orders');
    const data = await res.json();

    const tbody = document.getElementById('kitchen-orders-body');
    const msg = document.getElementById('kitchen-message');

    if (!res.ok) {
        msg.textContent = data.error || "Error loading orders";
        tbody.innerHTML = "";
        return;
    }

    if (data.length === 0) {
        tbody.innerHTML = "";
        msg.textContent = "No pending orders right now.";
        return;
    }

    msg.textContent = "";
    tbody.innerHTML = "";

    data.forEach(order => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${order.order_id}</td>
            <td>${order.student_name}</td>
            <td>${order.reg_id}</td>
            <td>${order.item_name}</td>
            <td>${order.quantity}</td>
            <td>${order.status}</td>
            <td>${order.order_time}</td>
            <td>
                <select onchange="updateOrder(${order.order_id}, this.value)">
                    <option value="">Change...</option>
                    <option value="PENDING">Pending</option>
                    <option value="PREPARING">Preparing</option>
                    <option value="READY">Ready</option>
                    <option value="DELIVERED">Delivered</option>
                    <option value="CANCELLED">Cancelled</option>
                </select>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function updateOrder(orderId, status) {
    if (!status) return;

    const res = await fetch('/kitchen/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: orderId, status: status })
    });

    const data = await res.json();
    const msg = document.getElementById('kitchen-message');

    if (res.ok) {
        msg.textContent = "✅ " + data.message;
        loadKitchenOrders();
    } else {
        msg.textContent = "❌ " + (data.error || "Error updating order");
    }
}

// initial load
window.onload = loadKitchenOrders;
