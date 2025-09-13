# Theme configuration for the PLC monitoring application

THEMES = {
    'dark': {
        'body_bg': '#0b1220',
        'body_color': '#e5e7eb',
        'panel_bg': '#0f172a',
        'panel_border': '#1f2937',
        'nav_bg': '#0b1220',
        'nav_hover': '#111827',
        'table_bg': '#0b1220',
        'table_row_alt': '#0f172a',
        'border_color': '#1f2937',
        'input_bg': '#111827',
        'input_border': '#253049',
        'text_primary': '#e5e7eb',
        'text_secondary': '#94a3b8',
        'text_muted': '#6b7280',
        'link_color': '#93c5fd',
        'btn_primary': '#2563eb',
        'btn_primary_hover': '#1d4ed8',
        'status_ok': '#28a745',
        'status_warning': '#f59e0b',
        'status_error': '#dc3545'
    },
    'light': {
        'body_bg': '#ffffff',
        'body_color': '#1f2937',
        'panel_bg': '#f9fafb',
        'panel_border': '#d1d5db',
        'nav_bg': '#ffffff',
        'nav_hover': '#f3f4f6',
        'table_bg': '#ffffff',
        'table_row_alt': '#f9fafb',
        'border_color': '#d1d5db',
        'input_bg': '#ffffff',
        'input_border': '#d1d5db',
        'text_primary': '#1f2937',
        'text_secondary': '#4b5563',
        'text_muted': '#9ca3af',
        'link_color': '#2563eb',
        'btn_primary': '#2563eb',
        'btn_primary_hover': '#1d4ed8',
        'status_ok': '#28a745',
        'status_warning': '#f59e0b',
        'status_error': '#dc3545'
    }
}

def get_theme_styles(theme_name='dark'):
    """Generate CSS variables and styles for the specified theme."""
    theme = THEMES.get(theme_name, THEMES['dark'])

    css_vars = []
    for key, value in theme.items():
        css_var_name = f'--{key.replace("_", "-")}'
        css_vars.append(f'{css_var_name}: {value};')

    return f':root {{ {" ".join(css_vars)} }}'

def get_current_theme():
    """Get the current theme from session or default to dark."""
    from flask import session
    return session.get('theme', 'dark')

def set_theme(theme_name):
    """Set the current theme in session."""
    from flask import session
    if theme_name in THEMES:
        session['theme'] = theme_name
        return True
    return False