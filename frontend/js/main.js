/**
 * Main dashboard logic for DRINKOO frontend.
 * Handles view navigation and data loading.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    // Set current user display
    const currentUser = getCurrentUser();
    document.getElementById('currentUser').textContent = `👤 ${currentUser.username}`;

    // Load initial data
    await loadDashboard();
    await loadStates();
    await loadSkus();
    await loadShipments();
    await loadReports();
});

/**
 * Navigate between views.
 */
function navigateTo(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));

    // Show selected view
    const view = document.getElementById(`${viewName}View`);
    if (view) {
        view.classList.add('active');
    }

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    event.target.classList.add('active');
}

/**
 * Load and display dashboard metrics.
 */
async function loadDashboard() {
    try {
        const data = await fetchDashboardMetrics();

        document.getElementById('totalCustomers').textContent = data.total_customers || 0;
        document.getElementById('totalSKUs').textContent = data.total_active_skus || 0;
        document.getElementById('pendingShipments').textContent = data.total_pending_shipments || 0;
        document.getElementById('statesCovered').textContent = data.total_states_covered || 0;
        document.getElementById('totalRevenue').textContent = formatCurrency(data.total_sales_revenue);
        document.getElementById('totalShipments').textContent = data.total_shipments || 0;
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

/**
 * Load and populate states dropdown.
 */
async function loadStates() {
    try {
        const states = await fetchStates();
        const stateSelector = document.getElementById('stateSelector');
        const shipmentState = document.getElementById('shipmentState');

        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state.state_code;
            option.textContent = state.state_name;

            stateSelector.appendChild(option);
            shipmentState.appendChild(option.cloneNode(true));
        });
    } catch (error) {
        console.error('Failed to load states:', error);
    }
}

/**
 * Load state-specific data when state is selected.
 */
async function loadStateData() {
    const stateCode = document.getElementById('stateSelector').value;
    if (!stateCode) return;

    try {
        const stateData = await fetchStateData(stateCode);
        const distribution = await fetchStateSkuDistribution(stateCode);

        // Update metrics
        document.getElementById('stateDataContainer').style.display = 'block';
        document.getElementById('stateCustomerCount').textContent = stateData.metrics.customer_count || 0;
        document.getElementById('stateSKUCount').textContent = stateData.metrics.available_sku_count || 0;
        document.getElementById('statePendingShipments').textContent = stateData.metrics.pending_shipments || 0;
        document.getElementById('stateRevenue').textContent = formatCurrency(stateData.metrics.total_revenue);
        document.getElementById('selectedStateName').textContent = stateData.state.state_name;

        // Populate SKU table
        const tbody = document.querySelector('#stateSkuTable tbody');
        tbody.innerHTML = '';

        distribution.sku_distribution.forEach(sku => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${sku.sku_code}</td>
                <td>${sku.flavor_profile}</td>
                <td>${sku.drink_size_ml}</td>
                <td>${sku.sku_category}</td>
                <td>${sku.quantity_allocated}</td>
                <td>${sku.distribution_percentage.toFixed(2)}%</td>
            `;
        });
    } catch (error) {
        console.error('Failed to load state data:', error);
    }
}

/**
 * Load and display SKUs.
 */
async function loadSkus() {
    try {
        const data = await fetchSkus({ status: 'active' });
        const tbody = document.querySelector('#skusTable tbody');
        tbody.innerHTML = '';

        // Also populate SKU selector for shipments
        const skuSelector = document.getElementById('shipmentSku');
        skuSelector.innerHTML = '<option value="">-- Select SKU --</option>';

        data.skus.forEach(sku => {
            // Add to table
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${sku.sku_code}</td>
                <td>${sku.sku_name}</td>
                <td>${sku.flavor_profile}</td>
                <td>${sku.drink_size_ml}</td>
                <td>${sku.sku_category}</td>
                <td>${formatCurrency(sku.manufacturing_cost_per_unit)}</td>
                <td>${formatCurrency(sku.shipping_cost_per_unit)}</td>
                <td>${formatCurrency(sku.retail_price)}</td>
            `;

            // Add to selector
            const option = document.createElement('option');
            option.value = sku.sku_id;
            option.textContent = `${sku.sku_code} - ${sku.sku_name}`;
            skuSelector.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load SKUs:', error);
    }
}

/**
 * Show the add SKU form.
 */
function showAddSkuForm() {
    document.getElementById('skuFormContainer').style.display = 'block';
}

/**
 * Hide the add SKU form.
 */
function hideAddSkuForm() {
    document.getElementById('skuFormContainer').style.display = 'none';
    document.getElementById('skuForm').reset();
}

/**
 * Handle SKU form submission.
 */
document.addEventListener('DOMContentLoaded', () => {
    const skuForm = document.getElementById('skuForm');
    if (skuForm) {
        skuForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const skuData = {
                sku_code: document.getElementById('skuCode').value,
                sku_name: document.getElementById('skuName').value,
                flavor_profile: document.getElementById('flavorProfile').value,
                drink_size_ml: parseInt(document.getElementById('drinkSize').value),
                manufacturing_cost_per_unit: parseFloat(document.getElementById('manufacturingCost').value),
                shipping_cost_per_unit: parseFloat(document.getElementById('shippingCost').value),
                retail_price: parseFloat(document.getElementById('retailPrice').value),
                sku_category: document.getElementById('skuCategory').value,
            };

            try {
                await createSku(skuData);
                alert('SKU created successfully!');
                hideAddSkuForm();
                await loadSkus();
            } catch (error) {
                alert(`Failed to create SKU: ${error.message}`);
            }
        });
    }
});

/**
 * Load and display shipments.
 */
async function loadShipments() {
    try {
        const data = await fetchShipments();
        const tbody = document.querySelector('#shipmentsTable tbody');
        tbody.innerHTML = '';

        data.shipments.forEach(shipment => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${shipment.shipment_tracking_code}</td>
                <td>${shipment.state_name || shipment.state_code}</td>
                <td>${shipment.sku_code}</td>
                <td>${shipment.quantity}</td>
                <td>${formatDate(shipment.shipment_date)}</td>
                <td><span class="status-badge status-${shipment.status}">${shipment.status}</span></td>
            `;
        });
    } catch (error) {
        console.error('Failed to load shipments:', error);
    }
}

/**
 * Show create shipment form.
 */
function showCreateShipmentForm() {
    document.getElementById('shipmentFormContainer').style.display = 'block';
}

/**
 * Hide create shipment form.
 */
function hideCreateShipmentForm() {
    document.getElementById('shipmentFormContainer').style.display = 'none';
    document.getElementById('shipmentForm').reset();
}

/**
 * Handle shipment form submission.
 */
document.addEventListener('DOMContentLoaded', () => {
    const shipmentForm = document.getElementById('shipmentForm');
    if (shipmentForm) {
        shipmentForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const shipmentData = {
                state_code: document.getElementById('shipmentState').value,
                sku_id: parseInt(document.getElementById('shipmentSku').value),
                quantity: parseInt(document.getElementById('shipmentQty').value),
                shipment_date: document.getElementById('shipmentDate').value,
                expected_delivery_date: document.getElementById('expectedDelivery').value || null,
            };

            try {
                await createShipment(shipmentData);
                alert('Shipment created successfully!');
                hideCreateShipmentForm();
                await loadShipments();
            } catch (error) {
                alert(`Failed to create shipment: ${error.message}`);
            }
        });
    }
});

/**
 * Track shipment by code.
 */
async function trackShipment() {
    const trackingCode = document.getElementById('trackingCodeInput').value.trim();
    if (!trackingCode) {
        alert('Please enter a tracking code');
        return;
    }

    try {
        const data = await fetch(`${API_BASE_URL}/shipments/${trackingCode}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
            },
        });

        if (!data.ok) throw new Error('Shipment not found');

        const result = await data.json();
        const tbody = document.querySelector('#shipmentDetailsBody');
        tbody.innerHTML = `
            <tr><th>Tracking Code</th><td>${result.shipment.shipment_tracking_code}</td></tr>
            <tr><th>State</th><td>${result.shipment.state_name || result.shipment.state_code}</td></tr>
            <tr><th>SKU</th><td>${result.shipment.sku_code} - ${result.shipment.sku_name}</td></tr>
            <tr><th>Quantity</th><td>${result.shipment.quantity}</td></tr>
            <tr><th>Shipment Date</th><td>${formatDate(result.shipment.shipment_date)}</td></tr>
            <tr><th>Status</th><td><span class="status-badge status-${result.shipment.status}">${result.shipment.status}</span></td></tr>
            <tr><th>Shipping Cost</th><td>${formatCurrency(result.shipment.shipping_cost)}</td></tr>
        `;
        document.getElementById('shipmentDetails').style.display = 'block';
    } catch (error) {
        alert(`Tracking failed: ${error.message}`);
    }
}

/**
 * Send chat message with RAG-enhanced response.
 */
async function sendChatMessage(event) {
    event.preventDefault();

    const chatInput = document.getElementById('chatInput');
    const question = chatInput.value.trim();
    if (!question) return;

    const messagesDiv = document.getElementById('chatMessages');

    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'chat-message user';
    userMessage.textContent = question;
    messagesDiv.appendChild(userMessage);

    chatInput.value = '';

    try {
        const data = await sendChatQuery(question);

        // Add assistant response with enhanced formatting
        const assistantMessage = document.createElement('div');
        assistantMessage.className = 'chat-message assistant';
        
        // Build enhanced message with confidence and source
        let messageHTML = `
            <div class="chat-response">
                <p class="chat-answer">${data.answer}</p>
                <div class="chat-metadata">
                    <span class="chat-source">📚 Source: ${data.source}</span>
                    <span class="chat-confidence confidence-${data.confidence.toLowerCase()}">
                        Confidence: ${data.confidence}
                    </span>
                </div>
        `;
        
        // Add context if available
        if (data.context && data.context.similarity && data.context.similarity > 0.5) {
            messageHTML += `
                <details class="chat-context">
                    <summary>Similar question in knowledge base</summary>
                    <p><strong>Q:</strong> ${data.context.question}</p>
                    <p><strong>Match:</strong> ${(data.context.similarity * 100).toFixed(0)}%</p>
                </details>
            `;
        }
        
        messageHTML += '</div>';
        assistantMessage.innerHTML = messageHTML;
        messagesDiv.appendChild(assistantMessage);

        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'chat-message assistant';
        errorMessage.innerHTML = `<div class="chat-error">❌ Error: ${error.message}</div>`;
        messagesDiv.appendChild(errorMessage);
    }
}

/**
 * Load and display reports.
 */
async function loadReports() {
    try {
        // Sales by state
        const salesByState = await fetchSalesByState();
        const salesTbody = document.querySelector('#salesByStateTable tbody');
        salesTbody.innerHTML = '';

        salesByState.forEach(state => {
            const row = salesTbody.insertRow();
            row.innerHTML = `
                <td>${state.state_name}</td>
                <td>${state.capital_city || '-'}</td>
                <td>${formatCurrency(state.total_revenue)}</td>
                <td>${state.total_units_sold}</td>
            `;
        });

        // Top SKUs
        const topSkus = await fetchTopSkus();
        const topTbody = document.querySelector('#topSkusTable tbody');
        topTbody.innerHTML = '';

        topSkus.forEach(sku => {
            const row = topTbody.insertRow();
            row.innerHTML = `
                <td>${sku.sku_code}</td>
                <td>${sku.sku_name}</td>
                <td>${sku.sku_category}</td>
                <td>${sku.total_units_sold}</td>
                <td>${formatCurrency(sku.total_revenue)}</td>
            `;
        });
    } catch (error) {
        console.error('Failed to load reports:', error);
    }
}
