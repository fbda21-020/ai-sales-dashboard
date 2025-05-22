import json
import dash
from dash import ALL, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
import logging
import bcrypt
import uuid
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import plotly.io as pio
pio.kaleido.scope.mathjax = None  
# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Secure User Loading ---
def load_users():
    try:
        users = pd.read_csv('users.csv')
        users['password_hash'] = users['password_hash'].astype(str)
        return users
    except FileNotFoundError:
        logger.error("users.csv not found. Creating empty user DataFrame.")
        return pd.DataFrame(columns=['username', 'password_hash', 'role'])
    except Exception as e:
        logger.error(f"Could not load users.csv: {e}")
        return pd.DataFrame(columns=['username', 'password_hash', 'role'])

users_df = load_users()

def verify_user(username, password):
    if not username or not password:
        return False
    user = users_df[users_df['username'] == username]
    if user.empty:
        return False
    hashed = user.iloc[0]['password_hash'].encode('utf-8')
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

# --- Data Loading ---
def load_data():
    try:
        df = pd.read_csv('test_dataPD.csv')
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        required_columns = [
            'date', 'country', 'continent', 'jobs_placed', 'scheduled_demos', 'ai_requests',
            'promotional_events', 'job_type', 'age_group', 'request_type'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")
        return df
    except FileNotFoundError:
        logger.error("Data file 'test_dataPD.csv' not found.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    logger.warning("Empty DataFrame loaded. Dashboard may have limited functionality.")

metric_map = {
    "jobs_placed": "Jobs Placed",
    "scheduled_demos": "Scheduled Demos",
    "ai_requests": "AI Requests",
    "promotional_events": "Promotional Events"
}
metrics = list(metric_map.keys())
continents = sorted(df['continent'].dropna().unique()) if not df.empty else []
countries = sorted(df['country'].dropna().unique()) if not df.empty else []
age_groups = sorted(df['age_group'].dropna().unique()) if not df.empty and 'age_group' in df.columns else []

# --- Custom CSS ---
CUSTOM_CSS = """
/* Core Styles */
body {
    background: #f5f6fa !important;
    font-family: 'Inter', 'Roboto', Arial, sans-serif !important;
    color: #111827 !important;
    height: 100vh !important;
    overflow: hidden !important;
    margin: 0 !important;
    display: flex;
    flex-direction: column;
}

/* Navigation */
.navbar-modern {
    background: #fff !important;
    border-bottom: 1px solid #e5e7eb !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
    padding: 16px 24px !important;
    min-height: 70px !important;
}
/* Modern Tab Bar Styling */
.tab-modern-container {
    background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.tab-modern {
    margin-top: 0 !important;
    border-bottom: none !important;
}

.tab-modern .nav-link {
    color: rgba(255,255,255,0.9) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    background: transparent !important;
    border-radius: 8px !important;
    margin-right: 6px !important;
    padding: 10px 20px !important;
    transition: all 0.3s ease !important;
    border: none !important;
    position: relative;
    overflow: hidden;
}

.tab-modern .nav-link::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 3px;
    background: white;
    transition: all 0.3s ease;
}

.tab-modern .nav-link:hover {
    background: rgba(255,255,255,0.15) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.tab-modern .nav-link:hover::before {
    width: 60%;
}

.tab-modern .nav-link.active {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.tab-modern .nav-link.active::before {
    width: 80%;
    background: #f59e0b;
}

.tab-modern .nav-link i {
    margin-right: 8px;
    font-size: 1.1rem;
}

.tab-modern .nav-link span {
    position: relative;
    top: 1px;
}
/* Modern Card Styling */
.card-modern {
    border-radius: 8px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.1) !important;
    border: none !important;
    background: linear-gradient(#fff, #f9fafb) !important;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    padding: 12px !important;
    margin: 0 !important;
}

/* Overview Tab Specific Styles */
.overview-metric-card {
    height: 110px !important;
    transition: all 0.3s ease !important;
    border-left: 4px solid #2563eb !important;
    padding: 0.5rem !important;
    text-align: center !important;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.overview-metric-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}

.overview-metric-icon {
    font-size: 1.5rem !important;
    margin-bottom: 0.25rem !important;
}

.overview-metric-title {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    margin: 0.1rem 0 !important;
    color: #374151 !important;
}

.overview-metric-value {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    margin: 0.25rem 0 !important;
}

#overview-jobs { color: #2563eb !important; }
#overview-demos { color: #10b981 !important; }
#overview-ai { color: #f59e0b !important; }
#overview-events { color: #8b5cf6 !important; }

.overview-metric-subtext {
    font-size: 0.65rem !important;
    color: #6b7280 !important;
}

/* Main Content Grid */
#overview-content-grid {
    display: flex;
    flex: 1;
    min-height: 0;
    margin-bottom: 20px;
}

#overview-activity-chart-container {
    flex: 0 0 55%;
    height: 220px;
    padding-right: 8px;
}

.quick-links-card {
    flex: 0 0 20%;
    height: 220px;
    overflow-y: auto;
    padding: 0 8px;
}

#overview-sparklines-container {
    flex: 0 0 25%;
    height: 220px;
    padding-left: 8px;
}

/* Graph Containers */
.dcc_graph {
    height: 100% !important;
    width: 100% !important;
    min-height: 0 !important;
}

/* Quick Links Styling */
.quick-links-list .list-group-item {
    padding: 0.5rem 1rem !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: 4px !important;
    margin-bottom: 0.25rem !important;
    transition: all 0.2s ease;
    cursor: pointer;
    background-color: #f9fafb !important;
}

.quick-links-list .list-group-item:hover {
    background-color: #e8f0fe !important;
    transform: translateX(2px);
}

/* Footer */
footer {
    background: #f5f6fa !important;
    padding: 12px !important;
    text-align: center !important;
    font-size: 0.7rem !important;
    color: #6b7280 !important;
    flex-shrink: 0;
}

/* Responsive Adjustments */
@media (max-width: 992px) {
    #overview-content-grid {
        flex-direction: column;
    }
    
    #overview-activity-chart-container,
    .quick-links-card,
    #overview-sparklines-container {
        flex: 1 1 auto;
        width: 100%;
        height: auto;
        min-height: 200px;
        padding: 0;
        margin-bottom: 16px;
    }
    
    .overview-metric-card {
        height: 100px !important;
    }
    
    .tab-modern .nav-link {
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
    }
}
/* Dropdown Styling Fixes */
.filter-dropdown {
    font-size: 0.8rem !important;
    height: 36px !important;
    min-height: 36px !important;
    border-radius: 6px !important;
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    padding: 0 8px !important;
    margin: 0 !important;
}

.filter-dropdown .Select-control {
    height: 36px !important;
    min-height: 36px !important;
}

.filter-dropdown .Select-value, 
.filter-dropdown .Select-placeholder {
    line-height: 36px !important;
    padding-top: 0 !important;
}

.filter-dropdown .Select-input {
    height: 36px !important;
}

.filter-label {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
    margin-bottom: 4px !important;
}

/* Date Picker (keep existing) */
.DateRangePicker {
    height: 26px !important;
}
"""
# --- App and Styling ---
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True
)
app.title = 'AI Sales Dashboard'
server = app.server

app.index_string = f"""
<!DOCTYPE html>
<html lang="en">
    <head>
        {{%metas%}}
        <title>{app.title}</title>
        {{%favicon%}}
        {{%css%}}
        <style>{CUSTOM_CSS}</style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

# --- Login Layout ---
login_card = dbc.Card(
    [
        dbc.CardBody([
            html.H2("LOGIN", className="text-center mb-4", style={
                "color": "#2563eb",  
                "fontWeight": "700",
                "fontSize": "2rem",  
                "letterSpacing": "0.1em"
            }),
            dbc.Label("Username", html_for="username", className="mb-1", style={"fontWeight": "500"}),
            dbc.InputGroup([
                dbc.InputGroupText(html.I(className="bi bi-person")),
                dbc.Input(id="username", type="text", placeholder="Enter username", style={"background": "#f9fafb"})
            ], className="mb-3"),
            dbc.Label("Password", html_for="password", className="mb-1", style={"fontWeight": "500"}),
            dbc.InputGroup([
                dbc.InputGroupText(html.I(className="bi bi-lock")),
                dbc.Input(id="password", type="password", placeholder="Enter password", style={"background": "#f9fafb"}),
                dbc.Button(html.I(className="bi bi-eye-slash"), id="toggle-password", outline=True, color="secondary", n_clicks=0)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Checkbox(id="remember-me", className="me-1"), width="auto"),
                dbc.Col(html.Span("Remember me", style={"fontSize": "0.95rem"}), width="auto")
            ], align="center", className="mb-3"),
            dbc.Button("Sign In", id="login-btn", color="primary", className="w-100", style={"fontWeight": "600", "fontSize": "1rem"}),
            html.Div(id="login-output", className="text-danger mt-2 text-center", style={"fontSize": "0.95rem"})
        ])
    ],
    className="card-modern",
    style={"maxWidth": "420px", "padding": "28px"}  
)


login_layout = html.Div(
    [
        html.Div(login_card, className="login-card-container")
    ],
    style={
        "background": "#f5f6fa",
        "height": "100vh",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center"
    }
)


# --- Tab Icons and Labels ---
TAB_ICONS = {
    "overview": "bi bi-speedometer2",  
    "geo": "bi bi-geo-alt",
    "time": "bi bi-clock-history",
    "age": "bi bi-people",
    "summary": "bi bi-pie-chart",
    "analytics": "bi bi-bar-chart-line"
}
TAB_LABELS = {
    "overview": "Dashboard",
    "geo": "Geography",
    "time": "Time Analysis",
    "age": "Age Groups",
    "summary": "Metric Proportions",
    "analytics": "Analytics"
}
TAB_ORDER = ["overview","geo", "time", "age", "summary", "analytics"]

# --- Dashboard Layout ---
def dashboard_layout():
    nav_tabs = dbc.Nav(
        [
            dbc.NavLink(
                [html.I(className=TAB_ICONS[tab]), html.Span(f" {TAB_LABELS[tab]}", className="ms-1")],
                id=f"tab-{tab}",
                href="#",
                className="nav-link",
            )
            for tab in TAB_ORDER
        ],
        pills=True,
        className="tab-modern mb-2"
    )
    
    topbar = dbc.Navbar(
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div([
                            html.I(className="bi bi-bar-chart-line navbar-brand-icon"),
                            html.Span("AI Sales Analytics", className="navbar-brand")
                        ], className="d-flex align-items-center"),
                        width="auto"
                    ),
                    dbc.Col(
                        html.Div([
                            html.I(className="bi bi-person-circle user-icon"),
                            html.Span(id="user-display", className="user-text"),
                            dbc.Button("Logout", id="logout-btn", color="danger", className="logout-btn"),
                        ], className="d-flex align-items-center justify-content-end"),
                        width=True
                    ),
                ],
                align="center",
                className="w-100",
                justify="between"
            ),
            fluid=True,
            className="px-0"
        ),
        className="navbar-modern",
        color="white",
        dark=False
    )
    
    footer = html.Footer(
        html.P("© 2025 AI Sales Dashboard ", style={"fontSize": "0.8rem", "color": "#6b7280"}),
        style={"background": "#f5f6fa", "padding": "8px", "textAlign": "center"}
    )
    
    return html.Div([
        topbar,
        dbc.Container([
            html.Div(
                nav_tabs,
                className="tab-modern-container",
                style={
                    "background": "linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%)",
                    "border-radius": "10px",
                    "padding": "10px",
                    "margin-bottom": "20px",
                    "box-shadow": "0 4px 12px rgba(0,0,0,0.1)"
                }
            ),
            html.Div(id="tab-content")
        ], fluid=True, style={"padding": "0 8px", "flexGrow": 1}),
        footer
    ], style={"background": "#f5f6fa", "height": "100vh", "display": "flex", "flexDirection": "column"})
# --- Tab Content Functions ---
def overview_tab():
    return html.Div([
        html.H3("Dashboard Overview", className="mb-3", style={
            "color": "#111827", 
            "fontWeight": "600",
            "marginTop": "10px"
        }),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-briefcase-fill overview-metric-icon", style={"color": "#2563eb"}),
                            html.H6("Jobs Placed", className="overview-metric-title")
                        ], className="d-flex flex-column align-items-center"),
                        html.H3(id="overview-jobs", className="overview-metric-value text-center mb-1"),
                        html.Small("Total placed", className="overview-metric-subtext text-center")
                    ], className="p-2")
                ], className="card-modern overview-metric-card border-start border-primary border-4"),
                md=3, className="pe-1"
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-calendar-check overview-metric-icon", style={"color": "#10b981"}),
                            html.H6("Scheduled Demos", className="overview-metric-title")
                        ], className="d-flex flex-column align-items-center"),
                        html.H3(id="overview-demos", className="overview-metric-value text-center mb-1"),
                        html.Small("Total scheduled", className="overview-metric-subtext text-center")
                    ], className="p-2")
                ], className="card-modern overview-metric-card border-start border-success border-4"),
                md=3, className="px-1"
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-robot overview-metric-icon", style={"color": "#f59e0b"}),
                            html.H6("AI Requests", className="overview-metric-title")
                        ], className="d-flex flex-column align-items-center"),
                        html.H3(id="overview-ai", className="overview-metric-value text-center mb-1"),
                        html.Small("Total requests", className="overview-metric-subtext text-center")
                    ], className="p-2")
                ], className="card-modern overview-metric-card border-start border-warning border-4"),
                md=3, className="px-1"
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-megaphone overview-metric-icon", style={"color": "#8b5cf6"}),
                            html.H6("Promo Events", className="overview-metric-title")
                        ], className="d-flex flex-column align-items-center"),
                        html.H3(id="overview-events", className="overview-metric-value text-center mb-1"),
                        html.Small("Total events", className="overview-metric-subtext text-center")
                    ], className="p-2")
                ], className="card-modern overview-metric-card border-start border-purple border-4"),
                md=3, className="ps-1"
            ),
        ], className="mb-3 g-0"),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(id="overview-activity-chart-title", className="py-2", style={"fontSize": "0.9rem"}),
                    dbc.CardBody([
                        dcc.Graph(
                            id="overview-activity-chart", 
                            style={"height": "280px"},
                            config={'displayModeBar': False}
                        )
                    ], className="p-1")
                ], className="card-modern"),
                md=8, className="pe-2"
            ),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Quick Navigation", className="py-2", style={"fontSize": "0.9rem"}),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem(
                                [html.I(className="bi bi-speedometer2 me-2"), "Dashboard"],
                                action=True,
                                id={"type": "quick-link", "index": "overview"},
                                className="border-0 rounded mb-1 py-2",
                                style={"fontSize": "0.8rem"}
                            ),
                            dbc.ListGroupItem(
                                [html.I(className="bi bi-geo-alt me-2"), "Geography"],
                                action=True,
                                id={"type": "quick-link", "index": "geo"},
                                className="border-0 rounded mb-1 py-2", 
                                style={"fontSize": "0.8rem"}
                            ),
                            dbc.ListGroupItem(
                                [html.I(className="bi bi-clock-history me-2"), "Time Analysis"],
                                action=True,
                                id={"type": "quick-link", "index": "time"},
                                className="border-0 rounded mb-1 py-2",
                                style={"fontSize": "0.8rem"}
                            ),
                            dbc.ListGroupItem(
                                [html.I(className="bi bi-download me-2"), "Export Data"],
                                action=True,
                                id={"type": "quick-link", "index": "export"},
                                className="border-0 rounded py-2",
                                style={"fontSize": "0.8rem"}
                            ),
                        ], flush=True)
                    ], style={"padding": "0.5rem"})
                ], className="card-modern mb-3"),
                
                dbc.Card([
                    dbc.CardHeader("Recent Highlights", className="py-2", style={"fontSize": "0.9rem"}),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Top Country: ", className="fw-bold", style={"fontSize": "0.85rem"}),
                                html.Span(id="top-country", className="text-primary", style={"fontSize": "0.85rem"})
                            ], className="mb-2"),
                            html.Div([
                                html.Span("Peak Day: ", className="fw-bold", style={"fontSize": "0.85rem"}),
                                html.Span(id="peak-day", className="text-primary", style={"fontSize": "0.85rem"})
                            ], className="mb-2"),
                            html.Div([
                                html.Span("Best Metric: ", className="fw-bold", style={"fontSize": "0.85rem"}),
                                html.Span(id="best-metric", className="text-primary", style={"fontSize": "0.85rem"})
                            ])
                        ], style={"padding": "0.25rem"})
                    ], style={"padding": "0.5rem"})
                ], className="card-modern")
            ], md=4, className="ps-2")
        ], className="g-0")
    ], style={
        "paddingBottom": "20px",
        "height": "calc(100vh - 150px)",
        "overflow": "hidden"
    })
       
def analytics_tab():
    min_date = df['date'].min() if not df.empty else dt(2000,1,1)
    max_date = df['date'].max() if not df.empty else dt.now()
    
    return html.Div([
        html.H3("Performance Analytics", className="mb-3", style={
            "color": "#111827",
            "fontWeight": "600",
            "fontSize": "1.5rem",
            "marginTop": "15px"  
        }),
        
        dbc.Row([
            dbc.Col([
                html.Div("Date Range", className="filter-label", style={"fontSize": "0.85rem"}),
                dcc.DatePickerRange(
                    id='analytics-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format="YYYY-MM-DD",
                    className="filter-dropdown",
                    style={"height": "36px"}
                )
            ], width=3, className="pe-2"),
            
            dbc.Col([
                html.Div("Metric", className="filter-label", style={"fontSize": "0.85rem"}),
                dcc.Dropdown(
                    id='analytics-metric',
                    options=[{"label": v, "value": k} for k, v in metric_map.items()],
                    value="jobs_placed",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "36px"}
                )
            ], width=2, className="pe-2"),
            
            dbc.Col([
                html.Div("Continent", className="filter-label", style={"fontSize": "0.85rem"}),
                dcc.Dropdown(
                    id='analytics-continent',
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "36px"}
                )
            ], width=2, className="pe-2"),
            
            dbc.Col(
                dbc.Button(
                    "Download Report",
                    id="analytics-export-btn",
                    color="primary",
                    className="mt-3",
                    style={"height": "36px"}
                ),
                width=2, className="pe-2"
            )
        ], className="mb-4 g-2"),  
        
        dcc.Loading(
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Total", className="mb-1 text-center", style={"fontSize": "0.9rem"}),
                        html.H2(id="analytics-total", className="text-center", style={
                            "color": "#2563eb",
                            "fontSize": "1.75rem",
                            "marginTop": "0.5rem"
                        })
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"), width=2, className="pe-1"),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Average", className="mb-1 text-center", style={"fontSize": "0.9rem"}),
                        html.H2(id="analytics-avg", className="text-center", style={
                            "color": "#2563eb", 
                            "fontSize": "1.75rem",
                            "marginTop": "0.5rem"
                        })
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"), width=2, className="pe-1"),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Maximum", className="mb-1 text-center", style={"fontSize": "0.9rem"}),
                        html.H2(id="analytics-max", className="text-center", style={
                            "color": "#2563eb",
                            "fontSize": "1.75rem",
                            "marginTop": "0.5rem"
                        })
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"), width=2, className="pe-1"),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Minimum", className="mb-1 text-center", style={"fontSize": "0.9rem"}),
                        html.H2(id="analytics-min", className="text-center", style={
                            "color": "#2563eb",
                            "fontSize": "1.75rem",
                            "marginTop": "0.5rem"
                        })
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"), width=2, className="pe-1"),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5("Std Dev", className="mb-1 text-center", style={"fontSize": "0.9rem"}),
                        html.H2(id="analytics-std", className="text-center", style={
                            "color": "#2563eb",
                            "fontSize": "1.75rem",
                            "marginTop": "0.5rem"
                        })
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"), width=2, className="pe-1"),
            ], className="mb-3 g-2"), 
            type="circle"
        ),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(id="analytics-gauge-1-title", className="mb-2 text-center", style={
                            "fontSize": "1rem",
                            "fontWeight": "500"
                        }),
                        dbc.Row([
                            dbc.Col(dcc.Graph(
                                id="analytics-gauge-1",
                                config={'displayModeBar': False},
                                style={"height": "200px"}
                            ), width=6, className="pe-1"),
                            dbc.Col(dcc.Graph(
                                id="analytics-gauge-2",
                                config={'displayModeBar': False},
                                style={"height": "200px"}
                            ), width=6, className="ps-1")
                        ], className="g-1")
                    ], style={"padding": "1rem"})
                ], className="card-modern", style={"height": "300px"}),
                width=5, className="pe-2"
            ),
            
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(id="analytics-heatmap-title", className="mb-2 text-center", style={
                            "fontSize": "1rem",
                            "fontWeight": "500"
                        }),
                        dcc.Graph(
                            id="analytics-heatmap",
                            config={'displayModeBar': False},
                            style={"height": "270px"}
                        )
                    ], style={"padding": "1rem"})
                ], className="card-modern", style={"height": "300px"}),
                width=7, className="ps-2"
            )
        ], className="g-3 mb-4")  
    ], style={"paddingBottom": "40px"})

# --- Geo Tab Layout ---
def geo_tab():
    return html.Div([
        html.H3("Geographic Performance", className="mb-3", style={
            "color": "#111827",
            "fontWeight": "600",
            "fontSize": "1.25rem"
        }),
        
        dbc.Row([
            dbc.Col([
                html.Div("Metric", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='geo-metric',
                    options=[{"label": v, "value": k} for k, v in metric_map.items()],
                    value="jobs_placed",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Continent", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='geo-continent',
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Country", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='geo-country',
                    options=[{"label": "All Countries", "value": "all"}],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"},
                    disabled=True
                )
            ], width=2, className="pe-1"),
            
            dbc.Col(
                dbc.Button(
                    "Download Report",
                    id="geo-export-btn",
                    color="primary",
                    className="mt-3",
                    style={"height": "32px"}
                ),
                width=2, className="pe-1"
            )
        ], className="mb-3 g-1"),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(id="geo-map-title", className="py-2", style={"fontSize": "0.9rem"}),
                    dbc.CardBody([
                        dcc.Graph(
                            id="geo-continent-map",
                            style={"height": "350px"},
                            config={'displayModeBar': False}
                        )
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"),
                md=6
            ),
            
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(id="geo-countries-title", className="py-2", style={"fontSize": "0.9rem"}),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.RadioItems(
                                    id='geo-performance-type',
                                    options=[
                                        {"label": "Top", "value": "top"},
                                        {"label": "Bottom", "value": "bottom"}
                                    ],
                                    value="top",
                                    inline=True,
                                    className="btn-group",
                                    inputClassName="btn-check",
                                    labelClassName="btn btn-sm btn-outline-primary",
                                    labelCheckedClassName="active"
                                )
                            ], width=6),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='geo-performance-count',
                                    options=[
                                        {'label': 'Show 5', 'value': 5},
                                        {'label': 'Show 10', 'value': 10}
                                    ],
                                    value=5,
                                    clearable=False,
                                    style={'width': '100%'}
                                )
                            ], width=6)
                        ], className="mb-2"),
                        dcc.Graph(
                            id="geo-countries-bar",
                            style={"height": "300px"},
                            config={'displayModeBar': False}
                        )
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"),
                md=6
            )
        ], className="g-2"),
        
        dcc.Download(id="geo-download-report")
    ], style={"paddingBottom": "30px"})
    
def time_tab():
    min_date = df['date'].min() if not df.empty else dt(2000,1,1)
    max_date = df['date'].max() if not df.empty else dt.now()
    
    return html.Div([
        html.H3("Time Trends Analysis", className="mb-3", style={
            "color": "#111827",
            "fontWeight": "600",
            "fontSize": "1.25rem"
        }),
        
        dbc.Row([
            dbc.Col([
                html.Div("Date Range", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.DatePickerRange(
                    id='time-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format="YYYY-MM-DD",
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=3, className="pe-1"),
            
            dbc.Col([
                html.Div("Metric", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='time-metric',
                    options=[{"label": v, "value": k} for k, v in metric_map.items()],
                    value="jobs_placed",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Continent", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='time-continent',
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Country", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='time-country',
                    options=[{"label": "All Countries", "value": "all"}],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"},
                    disabled=True
                )
            ], width=2, className="pe-1"),
            
            dbc.Col(
                dbc.Button(
                    "Download Report",
                    id="time-export-btn",
                    color="primary",
                    className="mt-3",
                    style={"height": "32px"}
                ),
                width=2, className="pe-1"
            )
        ], className="mb-3 g-1"),
        
        dbc.Row([
            dbc.Col([
                dbc.Label("Time Granularity", className="filter-label", style={"fontSize": "0.8rem"}),
                dbc.RadioItems(
                    id='time-granularity',
                    options=[
                        {"label": "Day", "value": "D"},
                        {"label": "Week", "value": "W"},
                        {"label": "Month", "value": "M"},
                        {"label": "Year", "value": "Y"}
                    ],
                    value="M",
                    inline=True,
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-sm btn-outline-primary",
                    labelCheckedClassName="active"
                )
            ], width=12, className="mb-3")
        ]),
        
        dbc.Card([
            dbc.CardHeader(
                html.Div(id='time-chart-title', className="mb-2", style={
                    "fontWeight": "500",
                    "fontSize": "1rem",
                    "color": "#2563eb"
                }), 
                className="py-2", 
                style={"fontSize": "0.9rem"}
            ),
            dbc.CardBody([
                dcc.Graph(
                    id="time-trend-chart",
                    style={"height": "350px"},  
                    config={'displayModeBar': False}
                )
            ], style={"padding": "0.75rem"})
        ], className="card-modern"),
        dcc.Download(id="time-download-report")
    ], style={"paddingBottom": "30px"})
    
def age_tab():
    return html.Div([
        html.H3("Age Group Analysis", className="mb-3", style={
            "color": "#111827",
            "fontWeight": "600",
            "fontSize": "1.25rem"
        }),
        
        dbc.Row([
            dbc.Col([
                html.Div("Metric", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='age-metric',
                    options=[{"label": v, "value": k} for k, v in metric_map.items()],
                    value="jobs_placed",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Continent", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='age-continent-filter',
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Country", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='age-country-filter',
                    options=[{"label": "All Countries", "value": "all"}],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"},
                    disabled=True
                )
            ], width=2, className="pe-1"),
            
            dbc.Col(
                dbc.Button(
                    "Download Report",
                    id="age-export-btn",
                    color="primary",
                    className="mt-3",
                    style={"height": "32px"}
                ),
                width=2, className="pe-1"
            )
        ], className="mb-3 g-1"),
        
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(id="age-bar-title", className="py-2"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="age-bar",
                            style={"height": "300px"},
                            config={'displayModeBar': False}
                        )
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"),
                md=6
            ),
            
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(id="age-pie-title", className="py-2"),
                    dbc.CardBody([
                        dcc.Graph(
                            id="age-pie",
                            style={"height": "300px"},
                            config={'displayModeBar': False}
                        )
                    ], style={"padding": "0.75rem"})
                ], className="card-modern"),
                md=6
            )
        ], className="g-2"),
        dcc.Download(id="age-download-report")
    ], style={"paddingBottom": "30px"})
    
def summary_tab():
    return html.Div([
        html.H3("Metric Analysis", className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div("Continent", className="filter-label"),
                dcc.Dropdown(
                    id="summary-continent",
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown"
                )
            ], width=2, className="pe-2"),
            
            dbc.Col([
                html.Div("Country", className="filter-label"),
                dcc.Dropdown(
                    id="summary-country",
                    options=[{"label": "All Countries", "value": "all"}],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    disabled=True
                )
            ], width=2, className="pe-2"),
            
            dbc.Col([
                html.Div("View Mode", className="filter-label"),
                dcc.Dropdown(
                    id="summary-view",
                    options=[
                        {"label": "Absolute Values", "value": "absolute"},
                        {"label": "Percentages", "value": "percentage"}
                    ],
                    value="absolute",
                    clearable=False,
                    className="filter-dropdown"
                )
            ], width=2, className="pe-2"),
            
            dbc.Col(
                dbc.Button(
                    "Download Report",
                    id="summary-export-btn",
                    color="primary",
                    className="mt-3"
                ),
                width=2, className="pe-2"
            )
        ], className="mb-3"),
        
        dcc.Loading([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader(id="summary-donut-title", className="py-2"),
                    dbc.CardBody([
                        dcc.Graph(id="summary-donut", style={"height": "320px"})
                    ])
                ], className="card-modern h-100"), width=12, md=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader(id="summary-stacked-bar-title", className="py-2"),
                    dbc.CardBody([
                        dcc.Graph(id="summary-stacked-bar", style={"height": "320px"})
                    ])
                ], className="card-modern h-100"), width=12, md=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader(id="summary-trend-title", className="py-2"),
                    dbc.CardBody([
                        dcc.Graph(id="summary-trend", style={"height": "320px"})
                    ])
                ], className="card-modern h-100"), width=12, md=4)
            ], className="g-2"),
            dcc.Download(id="summary-download-report")
        ])
    ])

@app.callback(
    Output('summary-donut-title', 'children'),
    Output('summary-stacked-bar-title', 'children'),
    Output('summary-trend-title', 'children'),
    Input('summary-continent', 'value'),
    Input('summary-country', 'value')
)
def update_summary_titles(continent, country):
    location_parts = []
    if continent != "all":
        location_parts.append(continent.title())
    if country != "all":
        location_parts.append(country.title())
    location_label = "Global" if not location_parts else " - ".join(location_parts)
    
    donut_title = f"Metric Distribution - {location_label}"
    bar_title = f"Metric Comparison - {location_label}"
    trend_title = f"Monthly Trends - {location_label}"
    
    return donut_title, bar_title, trend_title
    
def export_tab():
    min_date = df['date'].min() if not df.empty else dt(2000,1,1)
    max_date = df['date'].max() if not df.empty else dt.now()
    
    return html.Div([
        html.H3("Data Export", className="mb-3", style={
            "color": "#111827",
            "fontWeight": "600",
            "fontSize": "1.25rem"
        }),
        
        dbc.Row([
            dbc.Col([
                html.Div("Date Range", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.DatePickerRange(
                    id='export-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format="YYYY-MM-DD",
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=3, className="pe-1"),
            
            dbc.Col([
                html.Div("Metric", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='export-metric',
                    options=[{"label": "All Metrics", "value": "all"}] +
                            [{"label": v, "value": k} for k, v in metric_map.items()],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1"),
            
            dbc.Col([
                html.Div("Continent", className="filter-label", style={"fontSize": "0.8rem"}),
                dcc.Dropdown(
                    id='export-continent',
                    options=[{"label": "All Continents", "value": "all"}] +
                            [{"label": c.title(), "value": c} for c in continents],
                    value="all",
                    clearable=False,
                    className="filter-dropdown",
                    style={"height": "32px"}
                )
            ], width=2, className="pe-1")
        ], className="mb-3 g-1"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div(id='export-preview-header', children="Dataset Preview (First 10 rows)"), 
                        className="py-2", 
                        style={"fontSize": "0.9rem"}
                    ),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='export-preview',
                            columns=[{"name": i, "id": i} for i in df.columns],
                            data=df.head(10).to_dict('records'),
                            style_table={
                                'overflowX': 'auto',
                                'height': '300px',
                                'overflowY': 'auto'
                            },
                            style_cell={
                                'padding': '5px',
                                'fontSize': '0.75rem',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textAlign': 'left',
                                'maxWidth': '150px'
                            },
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': '600',
                                'fontSize': '0.8rem'
                            },
                            page_size=10
                        )
                    ], style={"padding": "0.5rem"})
                ], className="card-modern mb-3")
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Download Current View as CSV",
                    id="download-csv-btn",
                    color="primary",
                    className="w-100",
                    style={
                        "fontWeight": "600",
                        "maxWidth": "300px",
                        "margin": "0 auto",
                        "display": "block"
                    }
                ),
                dcc.Download(id="download-csv")
            ], width=12, className="text-center")
        ])
    ], style={"paddingBottom": "30px"})
#--- App Layout ---
app.layout = html.Div([
    dcc.Store(id='session-auth', storage_type='session'),
    dcc.Store(id='active-tab-store', data='overview'), 
    html.Div(id='page-content')
])

# --- Callbacks ---

# Login logic
@app.callback(
    Output('session-auth', 'data'),
    Output('login-output', 'children'),
    Input('login-btn', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    State('remember-me', 'value'),
    prevent_initial_call=True
)
def login(n_clicks, username, password, remember):
    if not username or not password:
        return dash.no_update, "Please enter both username and password."
    if verify_user(username, password):
        session_id = str(uuid.uuid4())
        auth_data = {'authenticated': True, 'user': username, 'session_id': session_id}
        if remember:
            auth_data['persistent'] = True
        return auth_data, ""
    else:
        return dash.no_update, "Invalid username or password."

# Logout logic
@app.callback(
    Output('session-auth', 'data', allow_duplicate=True),
    Input('logout-btn', 'n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks:
        return {'authenticated': False, 'user': None}
    return dash.no_update

# Toggle password visibility
@app.callback(
    Output('password', 'type'),
    Output('toggle-password', 'children'),
    Input('toggle-password', 'n_clicks'),
    State('password', 'type'),
    prevent_initial_call=True
)
def toggle_password(n_clicks, current_type):
    if current_type == "password":
        return "text", html.I(className="bi bi-eye")
    else:
        return "password", html.I(className="bi bi-eye-slash")

# Show dashboard or login
@app.callback(
    Output('page-content', 'children'),
    Input('session-auth', 'data')
)
def display_page(auth):
    if auth and auth.get('authenticated'):
        return dashboard_layout()
    else:
        return login_layout

@app.callback(
    Output('user-display', 'children'),
    Input('session-auth', 'data')
)
def update_user_display(auth):
    if auth and auth.get('user'):
        return f"Welcome, {auth['user'].capitalize()}"
    return "Welcome"

@app.callback(
    Output("active-tab-store", "data", allow_duplicate=True),
    Output("tab-content", "children"),
    [Input(f"tab-{tab}", "n_clicks") for tab in TAB_ORDER],
    [Input({"type": "quick-link", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def update_active_tab(*args):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return "overview", overview_tab()  
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id.startswith('{"index":'):
        try:
            tab_key = json.loads(triggered_id)['index']
            return tab_key, globals()[f"{tab_key}_tab"]()
        except:
            return "overview", overview_tab()
    
    if triggered_id.startswith('tab-'):
        tab_key = triggered_id.replace('tab-', '')
        if tab_key in TAB_ORDER:
            return tab_key, globals()[f"{tab_key}_tab"]()
    
    return "overview", overview_tab()

@app.callback(
    [Output("overview-jobs", "children"),
     Output("overview-demos", "children"),
     Output("overview-ai", "children"),
     Output("overview-events", "children"),
     Output("overview-activity-chart", "figure"),
     Output("top-country", "children"),
     Output("peak-day", "children"),
     Output("best-metric", "children")],  
    [Input('session-auth', 'data'),
     Input('active-tab-store', 'data')],
    prevent_initial_call=True
)
def update_overview_content(auth, active_tab):
    if df.empty or active_tab != 'overview':
        return ["0"] * 4, px.line(), "N/A", "N/A", "N/A"  
    
    try:
        metrics_data = [
            f"{df['jobs_placed'].sum():,}",
            f"{df['scheduled_demos'].sum():,}",
            f"{df['ai_requests'].sum():,}",
            f"{df['promotional_events'].sum():,}"
        ]
        
        activity_df = df.groupby(pd.Grouper(key='date', freq='W'))[metrics].sum().reset_index()
        activity_fig = px.line(
            activity_df, 
            x='date', 
            y=metrics,
            labels={'value': '', 'variable': ''},
            height=280  
        )
        activity_fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        top_country = df.groupby('country')['jobs_placed'].sum().idxmax()
        peak_day = df.loc[df['jobs_placed'].idxmax(), 'date'].strftime('%b %d, %Y')
        best_metric = max(metrics, key=lambda x: df[x].sum())
        
        return (
            *metrics_data,
            activity_fig,
            top_country,
            peak_day,
            metric_map.get(best_metric, best_metric)
        )
    
    except Exception as e:
        logger.error(f"Error updating overview: {e}")
        return ["0"] * 4, px.line(), "Error", "Error", "Error"  
# --- Analytics Tab Callbacks ---
@app.callback(
    Output('analytics-total', 'children'),
    Output('analytics-avg', 'children'),
    Output('analytics-max', 'children'),
    Output('analytics-min', 'children'),
    Output('analytics-std', 'children'),
    Output('analytics-gauge-1', 'figure'),
    Output('analytics-gauge-2', 'figure'),
    Output('analytics-heatmap', 'figure'),
    Input('analytics-date-range', 'start_date'),
    Input('analytics-date-range', 'end_date'),
    Input('analytics-metric', 'value'),
    Input('analytics-continent', 'value')
)
def update_analytics_tab(start_date, end_date, metric, continent):
    if df.empty or metric not in df.columns:
        return ["N/A"]*5, go.Figure(), go.Figure(), go.Figure()
    
    dff = df.copy()
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    
    if dff.empty:
        return ["No data"]*5, go.Figure(), go.Figure(), go.Figure()
    
    total = dff[metric].sum()
    avg = dff[metric].mean()
    mx = dff[metric].max()
    mn = dff[metric].min()
    std = dff[metric].std()
    
    gauge1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Total {metric_map.get(metric, metric)}", 'font': {'size': 12}},
        gauge={
            'axis': {'range': [0, mx*1.2], 'tickwidth': 1},
            'bar': {'color': "#2563eb"},
            'steps': [
                {'range': [0, mx*0.6], 'color': "#e8f0fe"},
                {'range': [mx*0.6, mx], 'color': "#bfdbfe"}
            ]
        }
    )).update_layout(
        margin=dict(t=30, b=10, l=20, r=20),
        height=160  
    )
    
    gauge2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=std,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Consistency (Std Dev)", 'font': {'size': 12}},
        gauge={
            'axis': {'range': [0, avg*2], 'tickwidth': 1},
            'bar': {'color': "#4f46e5"},
            'steps': [
                {'range': [0, avg*0.5], 'color': "#e9d5ff"},
                {'range': [avg*0.5, avg], 'color': "#d8b4fe"}
            ]
        }
    )).update_layout(
        margin=dict(t=30, b=10, l=20, r=20),
        height=160  
    )
    
    heatmap_df = dff.groupby(['country', pd.Grouper(key='date', freq='M')])[metric].sum().reset_index()
    if not heatmap_df.empty:
        pivot_df = heatmap_df.pivot(index='country', columns='date', values=metric).fillna(0)
        heatmap_fig = px.imshow(
            pivot_df,
            color_continuous_scale="Blues",
            labels=dict(x="Month", y="Country", color=metric_map.get(metric, metric)),
            height=220  
        )
        heatmap_fig.update_layout(
            margin=dict(l=50, r=20, t=30, b=50),
            xaxis_title="Month",
            yaxis_title="Country",
            coloraxis_colorbar=dict(
                title="",
                orientation="h",
                y=-0.2,
                thickness=10
            )
        )
    else:
        heatmap_fig = go.Figure()
    
    return (
        f"{total:,.0f}",
        f"{avg:,.2f}",
        f"{mx:,.0f}",
        f"{mn:,.0f}",
        f"{std:,.2f}",
        gauge1,
        gauge2,
        heatmap_fig
    )
# --- Geo Tab Callbacks ---
@app.callback(
    Output('geo-country', 'options'),
    Output('geo-country', 'disabled'),
    Output('geo-continent-map', 'figure'),
    Output('geo-countries-bar', 'figure'),
    Output('geo-map-title', 'children'),
    Input('geo-metric', 'value'),
    Input('geo-continent', 'value'),
    Input('geo-country', 'value'),
    Input('geo-performance-type', 'value'),
    Input('geo-performance-count', 'value'),
    prevent_initial_call=True
)
def update_geo_tab(metric, continent, country, performance_type, performance_count):
    if df.empty or metric not in df.columns:
        return [], True, go.Figure(), go.Figure(), "Select a metric"
    
    # Update country dropdown options and disabled state
    if continent == "all":
        country_options = [{"label": "All Countries", "value": "all"}]
        disabled = True
    else:
        countries_in_continent = df[df['continent'] == continent]['country'].unique()
        country_options = [{"label": "All Countries", "value": "all"}] + \
                         [{"label": c.title(), "value": c} for c in sorted(countries_in_continent)]
        disabled = False
    
    # Filter data based on selections
    dff = df.copy()
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if country != "all" and country is not None:  # Added check for None
        dff = dff[dff['country'] == country]
    
    # Generate dynamic title
    metric_label = metric_map.get(metric, metric)
    title_text = f"{metric_label} - "
    if continent == "all":
        title_text += "Global View"
    else:
        title_text += f"{continent.title()}"
        if country != "all" and country is not None:
            title_text += f" ({country.title()})"
    
    # Generate map figure
    map_df = dff.groupby('country')[metric].sum().reset_index()
    if not map_df.empty:
        map_fig = px.choropleth(
            map_df,
            locations="country",
            locationmode="country names",
            color=metric,
            hover_name="country",
            color_continuous_scale="Plasma"
        )
        map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    else:
        map_fig = go.Figure()
    
    # Generate bar chart figure
    countries_df = dff.groupby('country')[metric].sum().reset_index()
    if not countries_df.empty:
        if performance_type == "top":
            countries_df = countries_df.nlargest(performance_count, metric)
            color_seq = px.colors.sequential.Plasma[-performance_count:][::-1]
        else:
            countries_df = countries_df.nsmallest(performance_count, metric)
            color_seq = px.colors.sequential.Plasma[:performance_count]
        
        bar_fig = px.bar(
            countries_df, 
            x=metric, 
            y='country',
            orientation='h',
            color='country',
            color_discrete_sequence=color_seq
        )
        bar_fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})
    else:
        bar_fig = go.Figure()
    
    return country_options, disabled, map_fig, bar_fig, title_text
# --- Time Tab Callbacks ---
# Callback to update country dropdown in time tab
@app.callback(
    Output('time-country', 'options'),
    Output('time-country', 'disabled'),
    Input('time-continent', 'value')
)
def update_time_country_options(continent):
    if continent == "all":
        return [{"label": "All Countries", "value": "all"}], True
    else:
        countries_in_continent = df[df['continent'] == continent]['country'].unique()
        options = [{"label": "All Countries", "value": "all"}] + \
                 [{"label": c.title(), "value": c} for c in sorted(countries_in_continent)]
        return options, False

# Update time trend chart and title
@app.callback(
    Output('time-trend-chart', 'figure'),
    Output('time-chart-title', 'children'),
    Input('time-date-range', 'start_date'),
    Input('time-date-range', 'end_date'),
    Input('time-metric', 'value'),
    Input('time-continent', 'value'),
    Input('time-country', 'value'),
    Input('time-granularity', 'value'),
    prevent_initial_call=True
)
def update_time_tab(start_date, end_date, metric, continent, country, granularity):
    if df.empty or metric not in df.columns:
        return go.Figure(), "Select a metric"
    
    dff = df.copy()
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if country != "all":
        dff = dff[dff['country'] == country]
    
    if dff.empty:
        return go.Figure(), "No data available for selected filters"
    
    resampled = dff.set_index('date').resample(granularity)[metric].sum().reset_index()
    
    # Dynamic title parts
    metric_label = metric_map.get(metric, metric)
    granularity_map = {
        "D": "Daily",
        "W": "Weekly",
        "M": "Monthly",
        "Y": "Yearly"
    }
    granularity_label = granularity_map.get(granularity, granularity)
    
    region_parts = []
    if continent != "all":
        region_parts.append(continent.title())
    if country != "all":
        region_parts.append(country.title())
    region_label = "Globally" if not region_parts else "in " + ", ".join(region_parts)
    
    dynamic_title = f"{granularity_label} {metric_label} {region_label}"

    # Create line chart
    fig = px.line(
        resampled,
        x='date',
        y=metric,
        markers=True,
        line_shape="spline",
        color_discrete_sequence=["#2563eb"]
    )
    
    fig.update_layout(
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        margin=dict(l=50, r=20, t=30, b=50),
        xaxis_title="Date",
        yaxis_title=metric_label,
        hovermode="x unified",
        height=350
    )
    
    fig.update_traces(
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>%{y:,.0f}",
        line=dict(width=2)
    )
    
    if len(resampled) > 2:
        fig.add_trace(go.Scatter(
            x=resampled['date'],
            y=np.poly1d(np.polyfit(
                range(len(resampled)), 
                resampled[metric], 1)
            )(range(len(resampled))),
            line=dict(color="#ff7f0e", dash="dot", width=1.5),
            name="Trendline"
        ))
    
    return fig, dynamic_title

# --- Age Tab Callbacks ---
@app.callback(
    Output('age-country-filter', 'options'),
    Output('age-country-filter', 'disabled'),
    Input('age-continent-filter', 'value')
)
def update_age_country_options(continent):
    if continent == "all":
        return [{"label": "All Countries", "value": "all"}], True
    else:
        countries_in_continent = df[df['continent'] == continent]['country'].unique()
        options = [{"label": "All Countries", "value": "all"}] + \
                 [{"label": c.title(), "value": c} for c in sorted(countries_in_continent)]
        return options, False

@app.callback(
    Output('age-bar', 'figure'),
    Output('age-pie', 'figure'),
    Input('age-metric', 'value'),
    Input('age-continent-filter', 'value'),
    Input('age-country-filter', 'value')
)
def update_age_tab(metric, continent, country):
    if df.empty or 'age_group' not in df.columns or metric not in df.columns:
        return go.Figure(), go.Figure()
    
    dff = df.copy()

    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if country != "all":
        dff = dff[dff['country'] == country]

    if dff.empty:
        return go.Figure(), go.Figure()

    metric_label = metric_map.get(metric, metric)

    bar_df = dff.groupby('age_group')[metric].sum().reset_index()

    bar_fig = px.bar(
        bar_df,
        x='age_group',
        y=metric,
        color='age_group',
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={'age_group': 'Age Group', metric: metric_label},
        text=metric
    )
    bar_fig.update_layout(
        title=f"{metric_label} Across Age Groups",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Age Group",
        yaxis_title=metric_label
    )
    bar_fig.update_traces(
        texttemplate='%{y:,}',
        textposition='outside'
    )

    pie_fig = px.pie(
        bar_df,
        names='age_group',
        values=metric,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.3,
        labels={'value': metric_label}
    )
    pie_fig.update_layout(
        title=f"{metric_label} Share by Age Group",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return bar_fig, pie_fig

# --- Summary Tab Callbacks ---
@app.callback(
    Output('summary-country', 'options'),
    Output('summary-country', 'disabled'),
    Input('summary-continent', 'value')
)
def update_country_options(continent):
    if continent == "all":
        return [{"label": "All Countries", "value": "all"}], True
    else:
        countries_in_continent = df[df['continent'] == continent]['country'].unique()
        options = [{"label": "All Countries", "value": "all"}] + \
                 [{"label": c.title(), "value": c} for c in sorted(countries_in_continent)]
        return options, False

@app.callback(
    Output('summary-donut', 'figure'),
    Output('summary-stacked-bar', 'figure'),
    Output('summary-trend', 'figure'),
    Input('summary-continent', 'value'),
    Input('summary-country', 'value'),
    Input('summary-view', 'value')
)
def update_summary_tab(continent, country, view_type):
    if df.empty:
        return go.Figure(), go.Figure(), go.Figure()
    
    dff = df.copy()
    
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if country != "all":
        dff = dff[dff['country'] == country]
    
    totals = {metric: dff[metric].sum() for metric in metrics if metric in dff.columns}
    donut_fig = px.pie(
        names=[metric_map.get(m, m) for m in totals.keys()],
        values=list(totals.values()),
        hole=0.4,
        height=320
    )
    donut_fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        insidetextorientation='radial'
    )
    donut_fig.update_layout(
        margin=dict(l=30, r=30, t=40, b=30),
        uniformtext_minsize=10,
        uniformtext_mode='hide',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    group_by = 'continent' if continent == "all" else 'country'
    stacked_df = dff.groupby(group_by)[metrics].sum().reset_index()
    
    if view_type == "percentage":
        stacked_df[metrics] = stacked_df[metrics].div(stacked_df[metrics].sum(axis=1), axis=0)*100
    
    stacked_fig = px.bar(
        stacked_df,
        x=group_by,
        y=metrics,
        barmode='stack',
        height=320,
        labels={'value': 'Percentage' if view_type == "percentage" else 'Count'}
    )
    stacked_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=70),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        xaxis_title="",
        yaxis_title="Percentage" if view_type == "percentage" else "Count"
    )
    stacked_fig.update_xaxes(tickangle=-45)
    
    trend_df = dff.set_index('date').resample('M')[metrics].sum().reset_index()
    trend_fig = px.line(
        trend_df,
        x='date',
        y=metrics,
        height=320,
        labels={'value': 'Count'}
    )
    trend_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=70),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        xaxis_title="Month",
        yaxis_title="Count"
    )
    trend_fig.update_traces(
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f}"
    )
    
    return donut_fig, stacked_fig, trend_fig

# --- Export Data Callback ---
@app.callback(
    Output('export-preview', 'data'),
    Output('export-preview-header', 'children'),
    Input('export-date-range', 'start_date'),
    Input('export-date-range', 'end_date'),
    Input('export-metric', 'value'),
    Input('export-continent', 'value')
)
def update_export_preview(start_date, end_date, metric, continent):
    if df.empty:
        return [], "No data available"
    
    dff = df.copy()
    
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if metric != "all":
        columns_to_keep = ['date', 'country', 'continent', 'age_group', metric]
        dff = dff[[col for col in columns_to_keep if col in dff.columns]]
    
    filters_applied = any([
        start_date is not None,
        end_date is not None,
        continent != "all",
        metric != "all"
    ])
    
    header_text = "Filtered Dataset Preview" if filters_applied else "Dataset Preview (First 10 rows)"
    
    return dff.head(10).to_dict('records'), header_text


# Age Tab Download
@app.callback(
    Output("age-download-report", "data"),
    Input("age-export-btn", "n_clicks"),
    State("age-bar", "figure"),
    State("age-pie", "figure"),
    prevent_initial_call=True
)
def export_age_report(n_clicks, bar_fig, pie_fig):
    if not n_clicks:
        return dash.no_update
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Age Group Analysis Report", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        if bar_fig and 'data' in bar_fig:
            try:
                bar_img = pio.to_image(bar_fig, format="png", width=800, height=400, engine="kaleido")
                bar_img_buffer = io.BytesIO(bar_img)
                story.append(Paragraph("Performance by Age Group", styles['Heading2']))
                story.append(Image(bar_img_buffer, width=6*inch, height=3*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error exporting bar chart: {e}")
        
        if pie_fig and 'data' in pie_fig:
            try:
                pie_img = pio.to_image(pie_fig, format="png", width=800, height=400, engine="kaleido")
                pie_img_buffer = io.BytesIO(pie_img)
                story.append(Paragraph("Percentage Breakdown", styles['Heading2']))
                story.append(Image(pie_img_buffer, width=6*inch, height=3*inch))
            except Exception as e:
                logger.error(f"Error exporting pie chart: {e}")
        
        doc.build(story)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "age_group_report.pdf")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return dash.no_update

# Time Tab Download
@app.callback(
    Output("time-download-report", "data"),
    Input("time-export-btn", "n_clicks"),
    State("time-trend-chart", "figure"),
    prevent_initial_call=True
)
def export_time_report(n_clicks, trend_fig):
    if not n_clicks:
        return dash.no_update
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Time Trend Analysis Report", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        if trend_fig and 'data' in trend_fig:
            try:
                trend_img = pio.to_image(trend_fig, format="png", width=800, height=400, engine="kaleido")
                trend_img_buffer = io.BytesIO(trend_img)
                story.append(Paragraph("Trend Analysis", styles['Heading2']))
                story.append(Image(trend_img_buffer, width=6*inch, height=3*inch))
            except Exception as e:
                logger.error(f"Error exporting trend chart: {e}")
        
        doc.build(story)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "time_trend_report.pdf")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return dash.no_update

# Geo Tab Download
@app.callback(
    Output("geo-download-report", "data"),
    Input("geo-export-btn", "n_clicks"),
    State("geo-continent-map", "figure"),
    State("geo-countries-bar", "figure"),
    prevent_initial_call=True
)
def export_geo_report(n_clicks, map_fig, bar_fig):
    if not n_clicks:
        return dash.no_update
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Geographic Analysis Report", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        if map_fig and 'data' in map_fig:
            try:
                map_img = pio.to_image(map_fig, format="png", width=800, height=400, engine="kaleido")
                map_img_buffer = io.BytesIO(map_img)
                story.append(Paragraph("Geographic Distribution", styles['Heading2']))
                story.append(Image(map_img_buffer, width=6*inch, height=3*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error exporting map chart: {e}")
        
        if bar_fig and 'data' in bar_fig:
            try:
                bar_img = pio.to_image(bar_fig, format="png", width=800, height=400, engine="kaleido")
                bar_img_buffer = io.BytesIO(bar_img)
                story.append(Paragraph("Country Performance", styles['Heading2']))
                story.append(Image(bar_img_buffer, width=6*inch, height=3*inch))
            except Exception as e:
                logger.error(f"Error exporting bar chart: {e}")
        
        doc.build(story)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "geo_analysis_report.pdf")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return dash.no_update

# Analytics Tab Download
@app.callback(
    Output("analytics-download-report", "data"),
    Input("analytics-export-btn", "n_clicks"),
    State("analytics-gauge-1", "figure"),
    State("analytics-gauge-2", "figure"),
    State("analytics-heatmap", "figure"),
    prevent_initial_call=True
)
def export_analytics_report(n_clicks, gauge1_fig, gauge2_fig, heatmap_fig):
    if not n_clicks:
        return dash.no_update
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Performance Analytics Report", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        if gauge1_fig and 'data' in gauge1_fig:
            try:
                gauge1_img = pio.to_image(gauge1_fig, format="png", width=400, height=200, engine="kaleido")
                gauge1_img_buffer = io.BytesIO(gauge1_img)
                story.append(Paragraph("Total Metric Gauge", styles['Heading2']))
                story.append(Image(gauge1_img_buffer, width=3*inch, height=1.5*inch))
            except Exception as e:
                logger.error(f"Error exporting gauge 1: {e}")
        
        if gauge2_fig and 'data' in gauge2_fig:
            try:
                gauge2_img = pio.to_image(gauge2_fig, format="png", width=400, height=200, engine="kaleido")
                gauge2_img_buffer = io.BytesIO(gauge2_img)
                story.append(Paragraph("Consistency Gauge", styles['Heading2']))
                story.append(Image(gauge2_img_buffer, width=3*inch, height=1.5*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error exporting gauge 2: {e}")
        
        if heatmap_fig and 'data' in heatmap_fig:
            try:
                heatmap_img = pio.to_image(heatmap_fig, format="png", width=800, height=400, engine="kaleido")
                heatmap_img_buffer = io.BytesIO(heatmap_img)
                story.append(Paragraph("Performance Heatmap", styles['Heading2']))
                story.append(Image(heatmap_img_buffer, width=6*inch, height=3*inch))
            except Exception as e:
                logger.error(f"Error exporting heatmap: {e}")
        
        doc.build(story)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "analytics_report.pdf")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return dash.no_update

# Summary Tab Download
@app.callback(
    Output("summary-download-report", "data"),
    Input("summary-export-btn", "n_clicks"),
    State("summary-donut", "figure"),
    State("summary-stacked-bar", "figure"),
    State("summary-trend", "figure"),
    prevent_initial_call=True
)
def export_summary_report(n_clicks, donut_fig, bar_fig, trend_fig):
    if not n_clicks:
        return dash.no_update
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Metric Analysis Report", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        if donut_fig and 'data' in donut_fig:
            try:
                donut_img = pio.to_image(donut_fig, format="png", width=600, height=400, engine="kaleido")
                donut_img_buffer = io.BytesIO(donut_img)
                story.append(Paragraph("Metric Distribution", styles['Heading2']))
                story.append(Image(donut_img_buffer, width=4.5*inch, height=3*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error exporting donut chart: {e}")
        
        if bar_fig and 'data' in bar_fig:
            try:
                bar_img = pio.to_image(bar_fig, format="png", width=600, height=400, engine="kaleido")
                bar_img_buffer = io.BytesIO(bar_img)
                story.append(Paragraph("Metric Comparison", styles['Heading2']))
                story.append(Image(bar_img_buffer, width=4.5*inch, height=3*inch))
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error exporting bar chart: {e}")
        
        if trend_fig and 'data' in trend_fig:
            try:
                trend_img = pio.to_image(trend_fig, format="png", width=600, height=400, engine="kaleido")
                trend_img_buffer = io.BytesIO(trend_img)
                story.append(Paragraph("Monthly Trends", styles['Heading2']))
                story.append(Image(trend_img_buffer, width=4.5*inch, height=3*inch))
            except Exception as e:
                logger.error(f"Error exporting trend chart: {e}")
        
        doc.build(story)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "summary_report.pdf")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return dash.no_update
# Downloading the current view 
@app.callback(
    Output("download-csv", "data"),
    Input("download-csv-btn", "n_clicks"),
    State('export-date-range', 'start_date'),
    State('export-date-range', 'end_date'),
    State('export-metric', 'value'),
    State('export-continent', 'value'),
    prevent_initial_call=True
)
def download_csv(n_clicks, start_date, end_date, metric, continent):
    if df.empty:
        return None
    
    dff = df.copy()
    
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    if continent != "all":
        dff = dff[dff['continent'] == continent]
    if metric != "all":
        columns_to_keep = ['date', 'country', 'continent', 'age_group', metric]
        dff = dff[[col for col in columns_to_keep if col in dff.columns]]
    
    return dcc.send_data_frame(dff.to_csv, "exported_data.csv", index=False)
# --- Main ---
if __name__ == '__main__':
    app.run(debug=True)