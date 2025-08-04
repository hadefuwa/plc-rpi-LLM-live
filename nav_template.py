# Navigation template for consistent top navigation across all pages

NAV_TEMPLATE = '''
<nav class="top-nav">
    <div class="nav-container">
        <div class="nav-brand">
            <h1>E-Stop AI Status Reporter</h1>
        </div>
        <div class="nav-menu">
            <a href="/" class="nav-link {% if request.endpoint == "home" %}active{% endif %}">
                <i class="nav-icon">📊</i>
                Dashboard
            </a>
            <a href="/config" class="nav-link {% if request.endpoint == "config" %}active{% endif %}">
                <i class="nav-icon">⚙️</i>
                PLC Config
            </a>
            <a href="/status" class="nav-link {% if request.endpoint == "status" %}active{% endif %}">
                <i class="nav-icon">📈</i>
                System Status
            </a>
            <a href="/logs" class="nav-link {% if request.endpoint == "logs" %}active{% endif %}">
                <i class="nav-icon">📋</i>
                Event Logs
            </a>
        </div>
        <div class="nav-status">
            <span id="connectionStatus" class="status-indicator">
                <span class="status-dot"></span>
                Checking...
            </span>
        </div>
    </div>
</nav>
'''

NAV_STYLES = '''
.top-nav {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
}

.nav-brand h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: white;
}

.nav-menu {
    display: flex;
    gap: 20px;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 8px;
    color: rgba(255,255,255,0.8);
    text-decoration: none;
    padding: 12px 16px;
    border-radius: 6px;
    transition: all 0.3s ease;
    font-weight: 500;
}

.nav-link:hover {
    background: rgba(255,255,255,0.1);
    color: white;
    transform: translateY(-1px);
}

.nav-link.active {
    background: rgba(255,255,255,0.2);
    color: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.nav-icon {
    font-size: 16px;
}

.nav-status {
    display: flex;
    align-items: center;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ffc107;
    animation: pulse 2s infinite;
}

.status-dot.connected {
    background: #28a745;
    animation: none;
}

.status-dot.disconnected {
    background: #dc3545;
    animation: none;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Responsive design */
@media (max-width: 768px) {
    .nav-container {
        flex-direction: column;
        padding: 10px 20px;
        gap: 10px;
    }
    
    .nav-menu {
        gap: 10px;
    }
    
    .nav-link {
        padding: 8px 12px;
        font-size: 14px;
    }
    
    .nav-brand h1 {
        font-size: 20px;
    }
}
''' 