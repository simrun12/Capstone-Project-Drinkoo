/**
 * Authentication JavaScript for DRINKOO frontend.
 * Handles login and token management.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

/**
 * Handle login form submission.
 */
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');

    errorDiv.style.display = 'none';
    errorDiv.textContent = '';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Invalid username or password');
        }

        const data = await response.json();

        // Save token to localStorage
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('currentUser', JSON.stringify(data.user));

        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        errorDiv.style.display = 'block';
        errorDiv.textContent = error.message || 'Login failed. Please try again.';
        console.error('Login error:', error);
    }
}

/**
 * Get the authorization token from localStorage.
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Check if user is authenticated.
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Get current authenticated user.
 */
function getCurrentUser() {
    const userJson = localStorage.getItem('currentUser');
    return userJson ? JSON.parse(userJson) : null;
}

/**
 * Logout the current user.
 */
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

/**
 * Make an authenticated API request.
 */
async function makeAuthenticatedRequest(url, options = {}) {
    const token = getAuthToken();
    
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
    };

    return fetch(url, {
        ...options,
        headers,
    });
}
