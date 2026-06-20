/**
 * API client utilities for DRINKOO frontend.
 * Provides convenient wrappers for common API calls.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Fetch dashboard metrics.
 */
async function fetchDashboardMetrics() {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/analytics/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch dashboard metrics');
    return response.json();
}

/**
 * Fetch all states.
 */
async function fetchStates() {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/states`);
    if (!response.ok) throw new Error('Failed to fetch states');
    return response.json();
}

/**
 * Fetch state-specific data.
 */
async function fetchStateData(stateCode) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/states/${stateCode}/data`);
    if (!response.ok) throw new Error('Failed to fetch state data');
    return response.json();
}

/**
 * Fetch SKU distribution for a state.
 */
async function fetchStateSkuDistribution(stateCode) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/states/${stateCode}/sku-distribution`);
    if (!response.ok) throw new Error('Failed to fetch SKU distribution');
    return response.json();
}

/**
 * Fetch all SKUs.
 */
async function fetchSkus(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/skus${queryString ? '?' + queryString : ''}`;
    const response = await makeAuthenticatedRequest(url);
    if (!response.ok) throw new Error('Failed to fetch SKUs');
    return response.json();
}

/**
 * Create a new SKU.
 */
async function createSku(skuData) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/skus`, {
        method: 'POST',
        body: JSON.stringify(skuData),
    });
    if (!response.ok) throw new Error('Failed to create SKU');
    return response.json();
}

/**
 * Fetch all shipments.
 */
async function fetchShipments(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/shipments${queryString ? '?' + queryString : ''}`;
    const response = await makeAuthenticatedRequest(url);
    if (!response.ok) throw new Error('Failed to fetch shipments');
    return response.json();
}

/**
 * Create a new shipment.
 */
async function createShipment(shipmentData) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/shipments`, {
        method: 'POST',
        body: JSON.stringify(shipmentData),
    });
    if (!response.ok) throw new Error('Failed to create shipment');
    return response.json();
}

/**
 * Track a shipment by tracking code.
 */
async function trackShipment(trackingCode) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/shipments/${trackingCode}`);
    if (!response.ok) throw new Error('Shipment not found');
    return response.json();
}

/**
 * Update shipment status.
 */
async function updateShipmentStatus(trackingCode, status, deliveryDate = null) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/shipments/${trackingCode}/status`, {
        method: 'PUT',
        body: JSON.stringify({
            status,
            delivery_date: deliveryDate,
        }),
    });
    if (!response.ok) throw new Error('Failed to update shipment status');
    return response.json();
}

/**
 * Fetch sales by state.
 */
async function fetchSalesByState() {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/analytics/sales-by-state`);
    if (!response.ok) throw new Error('Failed to fetch sales by state');
    return response.json();
}

/**
 * Fetch top SKUs.
 */
async function fetchTopSkus(limit = 10) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/analytics/top-skus?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch top SKUs');
    return response.json();
}

/**
 * Send a chat message.
 */
async function sendChatQuery(question) {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/chatbot/ask?question=${encodeURIComponent(question)}`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error('Chat query failed');
    return response.json();
}

/**
 * Format currency value.
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
    }).format(value || 0);
}

/**
 * Format date value.
 */
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN');
}
