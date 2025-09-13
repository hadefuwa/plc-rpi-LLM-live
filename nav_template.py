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
            <a href="/reports" class="nav-link {% if request.endpoint == "reports" %}active{% endif %}">
                <i class="nav-icon">📝</i>
                Reports
            </a>
            <a href="/ai_config" class="nav-link {% if request.endpoint == "ai_config_page" %}active{% endif %}">
                <i class="nav-icon">🤖</i>
                AI Config
            </a>
        </div>
        <div class="nav-actions">
            <button id="themeToggle" class="theme-toggle" title="Toggle theme">
                <span class="theme-icon">🌙</span>
            </button>
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
    background: var(--nav-bg);
    color: var(--text-primary);
    padding: 0;
    box-shadow: 0 1px 2px rgba(0,0,0,.1);
    position: sticky;
    top: 0;
    z-index: 1000;
    border-bottom: 1px solid var(--border-color);
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
}

.nav-brand h1 { margin: 0; font-size: 20px; font-weight: 700; color: var(--text-primary); }

.nav-menu {
    display: flex;
    gap: 20px;
}

.nav-link { display: flex; align-items: center; gap: 8px; color: var(--text-secondary); text-decoration: none; padding: 12px 16px; border-radius: 6px; transition: background .2s ease; font-weight: 500; }
.nav-link:hover { background: var(--nav-hover); color: var(--text-primary); }
.nav-link.active { background: var(--nav-hover); color: var(--text-primary); box-shadow: inset 0 -2px 0 var(--btn-primary); }

.nav-icon {
    font-size: 16px;
}

.nav-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.theme-toggle {
    background: none;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: 6px;
    padding: 8px;
    cursor: pointer;
    transition: all .2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.theme-toggle:hover {
    background: var(--nav-hover);
    border-color: var(--btn-primary);
}

.theme-icon {
    font-size: 16px;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
}

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--status-warning); animation: pulse 2s infinite; }

.status-dot.connected {
    background: var(--status-ok);
    animation: none;
}

.status-dot.disconnected {
    background: var(--status-error);
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