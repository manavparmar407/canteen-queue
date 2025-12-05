// Load menu items
async function loadMenu() {
    const res = await fetch('/menu');
    const data = await res.json();

    const tbody = document.getElementById('menu-body');
    tbody.innerHTML = '';

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.item_id}</td>
            <td>${item.item_name}</td>
            <td>${item.category}</td>
            <td>${item.price}</td>
            <td>${item.avg_prep_time_minutes}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Submit order
async function submitOrder(event) {
    event.preventDefault();

    const body = {
        name: document.getElementById('name').value,
        reg_id: document.getElementById('reg_id').value,
        item_id: Number(document.getElementById('item_id').value),
        quantity: Number(document.getElementById('quantity').value || 1)
    };

    const res = await fetch('/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    const data = await res.json();
    const msg = document.getElementById('order-message');

    if (res.ok) {
        msg.textContent = `✅ ${data.message} (Order ID: ${data.order_id})`;
        document.getElementById('order-form').reset();
        loadQueueStatus();
        loadTodayStats();
    } else {
        msg.textContent = `❌ Error: ${data.error || 'Something went wrong'}`;
    }
}

// Load queue status
async function loadQueueStatus() {
    const res = await fetch('/queue-status');
    const data = await res.json();

    const div = document.getElementById('queue-status');

    if (data.message) {
        div.innerHTML = `<p>${data.message}</p>`;
    } else {
        div.innerHTML = `
            <p><strong>Snapshot Time:</strong> ${data.snapshot_time}</p>
            <p><strong>Pending Orders:</strong> ${data.pending_orders}</p>
            <p><strong>Average Wait Time:</strong> ${data.avg_wait_time_minutes} minutes</p>
        `;
    }
}

// Load today's stats
async function loadTodayStats() {
    const res = await fetch('/stats/today');
    const data = await res.json();

    const div = document.getElementById('today-stats');

    if (data.message) {
        div.innerHTML = `<p>${data.message}</p>`;
    } else {
        div.innerHTML = `
            <p><strong>Date:</strong> ${data.order_date}</p>
            <p><strong>Total Orders:</strong> ${data.total_orders}</p>
            <p><strong>Average Wait Time:</strong> ${Number(data.avg_wait_time).toFixed(2)} minutes</p>
        `;
    }
}

// On page load, load initial data
window.onload = function () {
    loadMenu();
    loadQueueStatus();
    loadTodayStats();
};
