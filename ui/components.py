"""
Medisynth Live – Premium UI Components
Animated SVG health gauge, sparkline mini-charts, risk prediction panel,
vital cards, AI reasoning, and emergency alert components.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional
import math


def _html(content: str):
    """Render HTML content reliably."""
    st.html(content)


# ──────────────────────────── Animated SVG Health Gauge ────────────────────────

def render_health_gauge(score: float, status_label: str, color: str, emoji: str):
    """Render a circular SVG health gauge with animated arc."""
    pct = max(0, min(100, score))
    radius = 70
    circumference = 2 * math.pi * radius
    dash = circumference * pct / 100
    gap = circumference - dash

    # Gradient colors based on score
    if pct >= 90:
        arc_color, glow = "#00d4aa", "rgba(0,212,170,0.3)"
    elif pct >= 75:
        arc_color, glow = "#4ade80", "rgba(74,222,128,0.3)"
    elif pct >= 60:
        arc_color, glow = "#fbbf24", "rgba(251,191,36,0.3)"
    elif pct >= 40:
        arc_color, glow = "#f97316", "rgba(249,115,22,0.3)"
    else:
        arc_color, glow = "#ff4757", "rgba(255,71,87,0.3)"

    _html(f"""
    <div style="text-align:center; padding:16px 0;">
        <div style="font-size:0.8rem; font-weight:600; text-transform:uppercase;
            letter-spacing:2px; color:#7986cb; margin-bottom:8px;">AI HEALTH SCORE</div>
        <svg width="200" height="200" viewBox="0 0 200 200" style="filter:drop-shadow(0 0 12px {glow});">
            <!-- Background circle -->
            <circle cx="100" cy="100" r="{radius}" fill="none"
                stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
            <!-- Animated arc -->
            <circle cx="100" cy="100" r="{radius}" fill="none"
                stroke="{arc_color}" stroke-width="10" stroke-linecap="round"
                stroke-dasharray="{dash:.1f} {gap:.1f}"
                transform="rotate(-90 100 100)"
                style="transition: stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1);">
                <animate attributeName="stroke-dasharray"
                    from="0 {circumference}" to="{dash:.1f} {gap:.1f}"
                    dur="1.2s" fill="freeze" />
            </circle>
            <!-- Score text -->
            <text x="100" y="90" text-anchor="middle" font-size="48"
                font-weight="900" fill="{arc_color}" font-family="Inter,sans-serif">{pct:.0f}</text>
            <text x="100" y="115" text-anchor="middle" font-size="12"
                font-weight="500" fill="#7986cb" font-family="Inter,sans-serif">/ 100</text>
        </svg>
        <div style="margin-top:4px;">
            <span style="background:rgba(255,255,255,0.06); padding:6px 16px; border-radius:20px;
                font-weight:600; font-size:1rem; color:{arc_color};">
                {emoji} {status_label}
            </span>
        </div>
    </div>
    """)


# ──────────────────────────── Sparkline Mini-Chart ────────────────────────────

def render_sparkline(data: List[float], color: str = "#00d4aa", height: int = 30, width: int = 120):
    """Render a tiny inline SVG sparkline chart."""
    if len(data) < 2:
        return ""
    recent = data[-20:]
    n = len(recent)
    mn, mx = min(recent), max(recent)
    rng = mx - mn if mx != mn else 1

    points = []
    for i, v in enumerate(recent):
        x = (i / (n - 1)) * width
        y = height - ((v - mn) / rng) * (height - 4) - 2
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    last_y = height - ((recent[-1] - mn) / rng) * (height - 4) - 2

    return f"""
    <svg width="{width}" height="{height}" style="display:inline-block; vertical-align:middle;">
        <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" opacity="0.7"/>
        <circle cx="{width}" cy="{last_y:.1f}" r="2.5" fill="{color}"/>
    </svg>
    """


# ──────────────────────────── Vital Card with Sparkline ───────────────────────

def render_vital_card(label: str, value: float, unit: str, icon: str = "💓",
                      color: str = "#00d4aa", trend: str = "→ Stable",
                      sparkline_data: List[float] = None):
    """Render a premium vital card with optional sparkline."""
    spark_svg = render_sparkline(sparkline_data, color) if sparkline_data and len(sparkline_data) > 2 else ""

    _html(f"""
    <div class="vital-card">
        <div class="vital-label">{icon} {label}</div>
        <div class="vital-value">{value:.1f}</div>
        <div class="vital-unit">{unit}</div>
        <div style="color:{color}; font-size:0.75rem; font-weight:500; margin-top:4px;">{trend}</div>
        {f'<div style="margin-top:8px;">{spark_svg}</div>' if spark_svg else ''}
    </div>
    """)


# ──────────────────────────── BP Card (Special) ──────────────────────────────

def render_bp_card(sys: float, dia: float, sparkline_data: List[float] = None):
    """Render a blood pressure card with systolic/diastolic."""
    color = "#f472b6"
    if sys > 140 or dia > 90:
        color = "#ff4757"
    elif sys < 90:
        color = "#ffb347"

    spark_svg = render_sparkline(sparkline_data, color) if sparkline_data and len(sparkline_data) > 2 else ""

    _html(f"""
    <div class="vital-card">
        <div class="vital-label">🩸 Blood Pressure</div>
        <div style="font-size:2.2rem; font-weight:800; color:{color}; line-height:1.1;">
            {sys:.0f}<span style="font-size:1.2rem; color:#7986cb;">/</span>{dia:.0f}
        </div>
        <div class="vital-unit">mmHg</div>
        {f'<div style="margin-top:8px;">{spark_svg}</div>' if spark_svg else ''}
    </div>
    """)


# ──────────────────────────── Risk Prediction Panel ──────────────────────────

def render_risk_prediction(prediction):
    """Render the 3-minute risk prediction panel."""
    if not prediction:
        return

    dir_color = {"improving": "#00d4aa", "stable": "#7986cb", "deteriorating": "#ff4757"}
    dir_icon = {"improving": "📈", "stable": "➡️", "deteriorating": "📉"}
    color = dir_color.get(prediction.trend_direction, "#7986cb")
    icon = dir_icon.get(prediction.trend_direction, "➡️")

    ttc_html = ""
    if prediction.time_to_critical_s:
        mins = prediction.time_to_critical_s / 60
        ttc_html = f"""
        <div style="color:#ff4757; font-weight:700; margin-top:8px; padding:8px;
            background:rgba(255,71,87,0.1); border-radius:8px; font-size:0.85rem;">
            ⏰ Estimated time to critical: {mins:.1f} min
        </div>"""

    _html(f"""
    <div class="glass-card" style="border-color:rgba(124,58,237,0.2);">
        <div class="section-header">🔮 3-Min Risk Prediction</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div>
                <div style="color:#7986cb; font-size:0.75rem;">TREND</div>
                <div style="color:{color}; font-weight:700; font-size:1.1rem;">
                    {icon} {prediction.trend_direction.upper()}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7986cb; font-size:0.75rem;">CONFIDENCE</div>
                <div style="color:#e8eaf6; font-weight:600;">{prediction.confidence:.0f}%</div>
            </div>
        </div>
        <div style="display:flex; gap:16px; font-size:0.85rem; color:#c5cae9;">
            <div>Predicted HR: <strong>{prediction.predicted_hr:.0f}</strong> bpm</div>
            <div>Predicted SpO₂: <strong>{prediction.predicted_spo2:.1f}</strong>%</div>
        </div>
        <div style="font-size:0.8rem; color:#7986cb; margin-top:4px;">
            HR Range: {prediction.hr_lower:.0f} – {prediction.hr_upper:.0f} bpm
        </div>
        {ttc_html}
    </div>
    """)


# ──────────────────────────── Session Timer ──────────────────────────────────

def render_session_info(session_id: str, elapsed_str: str, readings: int):
    """Render session info bar."""
    _html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center;
        padding:8px 16px; background:rgba(15,20,40,0.4); border-radius:10px;
        margin-bottom:12px; font-size:0.75rem; color:#7986cb;">
        <div>🔬 Session: <strong style="color:#a78bfa;">{session_id}</strong></div>
        <div>⏱️ {elapsed_str}</div>
        <div>📊 {readings} readings</div>
    </div>
    """)


# ──────────────────────────── AI Reasoning Panel ─────────────────────────────

def render_ai_reasoning(thinking_steps: list):
    """Render the AI thinking/reasoning panel."""
    steps_html = ""
    for step in thinking_steps:
        severity_color = {"info": "#c5cae9", "warning": "#ffb347", "critical": "#ff4757",
                          "monitoring": "#ffb347", "stable": "#00d4aa"}
        color = severity_color.get(step.severity, "#c5cae9")
        steps_html += f"""
        <div class="thinking-step">
            <span class="thinking-icon">{step.icon}</span>
            <span style="color:{color};">{step.message}</span>
        </div>"""

    _html(f"""
    <div class="thinking-panel">
        <div class="section-header">🧠 AI REASONING ENGINE</div>
        {steps_html}
    </div>
    """)


# ──────────────────────────── Detection Cards ────────────────────────────────

def render_detection_card(detection):
    """Render a single AI detection result."""
    sev_colors = {"critical": "#ff4757", "warning": "#ffb347", "info": "#00d4aa"}
    color = sev_colors.get(detection.severity, "#7986cb")

    evidence_html = "".join(f"<div style='color:#c5cae9; font-size:0.8rem;'>• {e}</div>" for e in detection.evidence)

    _html(f"""
    <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.02);
        border-left:3px solid {color}; border-radius:0 10px 10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="color:{color}; font-weight:700; font-size:0.9rem;">
                ⚠️ {detection.condition}
                <span style="font-size:0.7rem; color:#7986cb; margin-left:8px;">
                    ({detection.severity.upper()})
                </span>
            </div>
            <div style="color:#7986cb; font-size:0.75rem;">
                Confidence: {detection.confidence:.0f}%
            </div>
        </div>
        {evidence_html}
        <div style="color:#a78bfa; font-size:0.8rem; margin-top:4px; font-style:italic;">
            → {detection.recommendation}
        </div>
    </div>
    """)


# ──────────────────────────── Score Breakdown ────────────────────────────────

def render_score_breakdown(breakdown: list):
    """Render health score breakdown items."""
    items_html = ""
    for item in breakdown:
        ded_color = "#ff4757" if item.deduction > 0 else "#00d4aa"
        ded_text = f"-{item.deduction:.1f}" if item.deduction > 0 else "✓ 0"
        weight_pct = f"{item.weight * 100:.0f}%"
        items_html += f"""
        <div class="breakdown-item">
            <div class="breakdown-label">
                {item.icon} {item.category}
                <span style="color:#4a5568; font-size:0.7rem; margin-left:4px;">({weight_pct})</span>
            </div>
            <div class="breakdown-deduction {'deduction-negative' if item.deduction > 0 else 'deduction-zero'}">
                {ded_text}
            </div>
        </div>"""

    _html(f"""
    <div class="glass-card">
        <div class="section-header">❓ WHY THIS SCORE?</div>
        {items_html}
    </div>
    """)


# ──────────────────────────── Status Banner ──────────────────────────────────

def render_status_banner(status: str):
    """Render system status banner."""
    status_map = {
        "stable": ("🟢", "SYSTEM STATUS: STABLE", "status-stable"),
        "monitoring": ("🟡", "SYSTEM STATUS: MONITORING", "status-monitoring"),
        "critical": ("🔴", "SYSTEM STATUS: CRITICAL", "status-critical"),
    }
    emoji, text, css_class = status_map.get(status, status_map["stable"])
    _html(f"""
    <div class="status-banner {css_class}">
        <span style="font-size:1.2rem;">{emoji}</span>
        <strong>{text}</strong>
        <span style="font-size:0.8rem; opacity:0.7;">• Medisynth Live Active</span>
    </div>
    """)


# ──────────────────────────── Emergency Alert Card ───────────────────────────

def render_alert_card(alert, contacts, key_notify, key_confirm, key_dismiss):
    """Render emergency alert with 3-step workflow."""
    step = alert.step
    step1 = "✓ Alert User" if step >= 1 else "○ Alert User"
    step2 = "✓ Notify Contacts" if step >= 2 else "○ Notify Contacts"
    step3 = "✓ Confirmed" if step >= 3 else "○ Confirmed"

    step1_color = "#00d4aa" if step >= 1 else "#7986cb"
    step2_color = "#00d4aa" if step >= 2 else "#7986cb"
    step3_color = "#00d4aa" if step >= 3 else "#7986cb"

    _html(f"""
    <div class="alert-card">
        <div class="alert-title">🚨 Emergency Alert Active</div>
        <div style="color:#c5cae9; font-size:0.85rem; margin-bottom:12px;">
            Health Score: <strong style="color:#ff4757;">{alert.health_score:.0f}</strong> |
            HR: <strong>{alert.heart_rate:.0f}</strong> bpm |
            SpO₂: <strong>{alert.spo2:.1f}</strong>%
        </div>
        <div style="display:flex; gap:16px; font-size:0.85rem; margin-bottom:12px;">
            <span style="color:{step1_color}; font-weight:600;">{step1}</span>
            <span style="color:{step2_color}; font-weight:600;">{step2}</span>
            <span style="color:{step3_color}; font-weight:600;">{step3}</span>
        </div>
    </div>
    """)

    col1, col2 = st.columns(2)
    if step == 1:
        with col1:
            if st.button("📤 Notify Emergency Contacts", key=key_notify):
                return "notify"
    elif step == 2:
        with col1:
            if st.button("✓ Confirm Alert Sent", key=key_confirm):
                return "confirm"

    if step < 3:
        with col2:
            if st.button("✕ Dismiss Alert", key=key_dismiss):
                return "dismiss"

    if step >= 3:
        _html("""
            <div style="color:#00d4aa; font-size:0.9rem; padding:8px 0;">
                ✓ Alert confirmed and contacts notified
            </div>
        """)

    return None


# ──────────────────────────── Confidence Badge ───────────────────────────────

def render_confidence_badge(confidence: float, noise: float = 0):
    """Render data confidence badge."""
    color = "#00d4aa" if confidence >= 85 else "#ffb347" if confidence >= 60 else "#ff4757"
    level = "High" if confidence >= 85 else "Medium" if confidence >= 60 else "Low"
    _html(f"""
    <div class="glass-card">
        <div class="section-header">📡 Data Reliability</div>
        <div style="text-align:center;">
            <div style="font-size:2rem; font-weight:800; color:{color};">{confidence:.0f}%</div>
            <div style="color:#7986cb; font-size:0.8rem;">({level})</div>
        </div>
        {f'<div style="color:#4a5568; font-size:0.75rem; text-align:center; margin-top:4px;">Noise: {noise:.3f}</div>' if noise > 0 else ''}
    </div>
    """)


# ──────────────────────────── Anomaly Score Indicator ────────────────────────

def render_anomaly_score(score: float):
    """Render the composite anomaly score as a horizontal bar."""
    pct = score * 100
    color = "#00d4aa" if pct < 20 else "#ffb347" if pct < 50 else "#ff4757"
    label = "Normal" if pct < 20 else "Elevated" if pct < 50 else "High"
    _html(f"""
    <div class="glass-card">
        <div class="section-header">🎯 Anomaly Score</div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="flex:1;">
                <div style="width:100%; height:8px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden;">
                    <div style="width:{pct:.0f}%; height:100%; background:{color}; border-radius:4px;
                        transition:width 0.8s ease;"></div>
                </div>
            </div>
            <div style="color:{color}; font-weight:700; font-size:0.9rem; min-width:60px; text-align:right;">
                {pct:.0f}% {label}
            </div>
        </div>
    </div>
    """)


# ──────────────────────────── Event Timeline ─────────────────────────────────

def render_event_timeline(events: list, max_events: int = 8):
    """Render a vertical event timeline."""
    if not events:
        _html("""
        <div class="glass-card">
            <div class="section-header">📋 Event Timeline</div>
            <div style="color:#7986cb; font-size:0.85rem;">No events yet</div>
        </div>
        """)
        return

    import datetime
    items_html = ""
    for ev in reversed(events[-max_events:]):
        ts = datetime.datetime.fromtimestamp(ev.timestamp).strftime("%H:%M:%S")
        sev_colors = {"critical": "#ff4757", "warning": "#ffb347", "info": "#00d4aa"}
        color = sev_colors.get(ev.severity, "#7986cb")
        type_icons = {"detection": "⚠️", "mode_change": "🔄", "alert": "🚨", "baseline": "📊"}
        icon = type_icons.get(ev.event_type, "•")

        items_html += f"""
        <div style="display:flex; gap:10px; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);
            font-size:0.8rem; animation:fadeSlideIn 0.3s ease-out;">
            <div style="color:#4a5568; min-width:55px; font-family:'JetBrains Mono',monospace;">{ts}</div>
            <div style="color:{color}; min-width:20px;">{icon}</div>
            <div style="color:#c5cae9; flex:1;">{ev.title}</div>
        </div>"""

    _html(f"""
    <div class="glass-card">
        <div class="section-header">📋 Event Timeline</div>
        {items_html}
    </div>
    """)


# ──────────────────────────── Vitals Chart ───────────────────────────────────

def create_vitals_chart(timestamps: list, hr_data: list, spo2_data: list,
                        hr_raw: list = None, spo2_raw: list = None,
                        show_raw: bool = False) -> go.Figure:
    """Create premium Plotly chart for vital signs."""
    fig = go.Figure()

    x_labels = list(range(len(hr_data)))

    if show_raw and hr_raw:
        fig.add_trace(go.Scatter(
            x=x_labels, y=hr_raw, mode='lines', name='HR (Raw)',
            line=dict(color='rgba(255, 179, 71, 0.3)', width=1, dash='dot'),
            hovertemplate='HR Raw: %{y:.1f} bpm<extra></extra>',
        ))
    if show_raw and spo2_raw:
        fig.add_trace(go.Scatter(
            x=x_labels, y=spo2_raw, mode='lines', name='SpO₂ (Raw)',
            line=dict(color='rgba(167, 139, 250, 0.3)', width=1, dash='dot'),
            yaxis='y2',
            hovertemplate='SpO₂ Raw: %{y:.1f}%<extra></extra>',
        ))

    # Processed HR
    fig.add_trace(go.Scatter(
        x=x_labels, y=hr_data, mode='lines', name='Heart Rate',
        line=dict(color='#00d4aa', width=2.5, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 170, 0.05)',
        hovertemplate='HR: %{y:.1f} bpm<extra></extra>',
    ))

    # Processed SpO₂
    fig.add_trace(go.Scatter(
        x=x_labels, y=spo2_data, mode='lines', name='SpO₂',
        line=dict(color='#a78bfa', width=2.5, shape='spline'),
        yaxis='y2',
        hovertemplate='SpO₂: %{y:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#0f1428',
        font=dict(family='Inter, sans-serif', color='#7986cb', size=11),
        height=340,
        margin=dict(l=50, r=50, t=30, b=30),
        legend=dict(
            orientation='h', yanchor='top', y=1.12, xanchor='center', x=0.5,
            bgcolor='rgba(10,14,26,0.9)', font=dict(size=11),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            showticklabels=False,
        ),
        yaxis=dict(
            title=dict(text='Heart Rate (bpm)', font=dict(color='#00d4aa', size=11)),
            showgrid=True, gridcolor='rgba(255,255,255,0.03)',
            zeroline=False, tickfont=dict(color='#00d4aa'),
        ),
        yaxis2=dict(
            title=dict(text='SpO₂ (%)', font=dict(color='#a78bfa', size=11)),
            overlaying='y', side='right',
            showgrid=False, zeroline=False,
            tickfont=dict(color='#a78bfa'),
            range=[80, 102],
        ),
        hovermode='x unified',
    )

    return fig


def create_score_history_chart(scores: list) -> go.Figure:
    """Create a small health score trend chart."""
    fig = go.Figure()
    x = list(range(len(scores)))

    # Color gradient based on score
    colors = ['#ff4757' if s < 40 else '#f97316' if s < 60 else '#fbbf24' if s < 75 else '#4ade80' if s < 90 else '#00d4aa' for s in scores]

    fig.add_trace(go.Scatter(
        x=x, y=scores, mode='lines+markers',
        line=dict(color='#a78bfa', width=2, shape='spline'),
        marker=dict(size=3, color=colors),
        fill='tozeroy', fillcolor='rgba(167,139,250,0.05)',
        hovertemplate='Score: %{y:.0f}<extra></extra>',
    ))

    # Critical threshold line
    fig.add_hline(y=40, line=dict(color='rgba(255,71,87,0.3)', width=1, dash='dash'))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#0f1428',
        font=dict(family='Inter, sans-serif', color='#7986cb', size=10),
        height=180,
        margin=dict(l=40, r=20, t=10, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 105], showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                   zeroline=False, tickfont=dict(color='#7986cb')),
        showlegend=False,
    )
    return fig


# ──────────────────────────── Medisynth Engine Panel ─────────────────────────

def render_medisynth_panel(synthetic_engine, analytics, mode: str):
    """Render the Medisynth AI Engine dedicated panel."""
    is_training = synthetic_engine.is_training_mode
    active = synthetic_engine.get_active_scenario_info()
    scenario_name = active.name if active else "—"
    total_readings = analytics.total_readings if analytics else 0

    phase_label = "Synthetic Training" if is_training else "Live Monitoring"
    phase_color = "#a78bfa" if is_training else "#00d4aa"
    phase_icon = "🧬" if is_training else "📡"

    edge_cases = "YES" if (active or is_training) else "NO"
    edge_color = "#fbbf24" if edge_cases == "YES" else "#7986cb"

    _html(f"""
    <div class="glass-card" style="border-color:rgba(124,58,237,0.2);">
        <div class="section-header">🧬 MEDISYNTH AI ENGINE</div>

        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px;">PHASE</div>
                <div style="color:{phase_color}; font-weight:700; font-size:0.95rem;">
                    {phase_icon} {phase_label}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px;">SCENARIO</div>
                <div style="color:#e8eaf6; font-weight:600; font-size:0.9rem;">{scenario_name}</div>
            </div>
        </div>

        <div style="display:flex; gap:12px; margin-bottom:10px;">
            <div style="flex:1; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center;">
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;
                    font-family:'JetBrains Mono',monospace;">{total_readings}</div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase;">Samples Generated</div>
            </div>
            <div style="flex:1; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center;">
                <div style="color:{edge_color}; font-size:1.3rem; font-weight:800;">{edge_cases}</div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase;">Edge Cases Injected</div>
            </div>
        </div>

        <div style="display:flex; gap:8px; font-size:0.7rem;">
            <div style="flex:1; padding:6px 8px; border-radius:6px;
                background:{'rgba(167,139,250,0.15)' if is_training else 'rgba(255,255,255,0.03)'};
                border:1px solid {'rgba(167,139,250,0.3)' if is_training else 'transparent'};
                color:{'#a78bfa' if is_training else '#4a5568'}; text-align:center; font-weight:600;">
                🧬 Training Phase<br><span style="font-size:0.6rem;">Synthetic Data (Medisynth)</span>
            </div>
            <div style="flex:1; padding:6px 8px; border-radius:6px;
                background:{'rgba(0,212,170,0.15)' if not is_training else 'rgba(255,255,255,0.03)'};
                border:1px solid {'rgba(0,212,170,0.3)' if not is_training else 'transparent'};
                color:{'#00d4aa' if not is_training else '#4a5568'}; text-align:center; font-weight:600;">
                📡 Live Phase<br><span style="font-size:0.6rem;">Streaming Wearable Data</span>
            </div>
        </div>
    </div>
    """)


# ──────────────────────────── Data Source Label ───────────────────────────────

def render_data_source_label(mode: str):
    """Render the 'Physiologically simulated data' badge."""
    _html(f"""
    <div style="display:flex; align-items:center; gap:8px; padding:4px 12px;
        background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.15);
        border-radius:8px; margin-bottom:8px; font-size:0.7rem; color:#a78bfa;">
        <span>🧬</span>
        <span>Physiologically simulated data (not random) — Mode: <strong>{mode.upper()}</strong></span>
        <span style="margin-left:auto; font-size:0.6rem; color:#7986cb;">2s intervals</span>
    </div>
    """)


# ──────────────────────────── Enhanced Emergency Notification ────────────────

def render_emergency_notification(alert, contacts, location=None):
    """Render emergency notification with REAL location."""
    import datetime
    ts = datetime.datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")

    contacts_html = ""
    for c in contacts:
        contacts_html += f"""
        <div style="display:flex; align-items:center; gap:10px; padding:8px 0;
            border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.8rem;">
            <span style="color:#00d4aa; font-size:1rem;">✔</span>
            <div style="flex:1;">
                <div style="color:#e8eaf6; font-weight:600;">{c.name}</div>
                <div style="color:#7986cb; font-size:0.7rem;">{c.phone} • {c.relationship}</div>
            </div>
            <div style="color:#00d4aa; font-size:0.7rem; font-weight:600;">✔ Notified</div>
        </div>"""

    if not contacts:
        contacts_html = '<div style="color:#ffb347; font-size:0.8rem; padding:8px 0;">⚠️ No contacts. Add in sidebar.</div>'

    # REAL location
    if location and location.get("lat") and location["lat"] != 0:
        maps_link = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"
        city = f"{location.get('city','')} {location.get('region','')}, {location.get('country','')}".strip()
        loc_html = f'📍 <a href="{maps_link}" target="_blank" style="color:#00d4aa; text-decoration:underline;">Open Map</a> — {city} ({location["lat"]:.4f}, {location["lng"]:.4f})'
    elif alert.google_maps_link:
        loc_html = f'📍 <a href="{alert.google_maps_link}" target="_blank" style="color:#00d4aa;">{alert.google_maps_link}</a>'
    else:
        loc_html = '<span style="color:#ffb347;">📍 Acquiring location...</span>'

    _html(f"""
    <div style="background:rgba(255,71,87,0.06); border:1px solid rgba(255,71,87,0.2);
        border-radius:16px; padding:20px; margin:8px 0; animation:pulse-critical 2s infinite;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <span style="font-size:1.3rem;">🚨</span>
            <span style="color:#ff4757; font-size:1rem; font-weight:700;">EMERGENCY ALERT DISPATCHED</span>
            <span style="margin-left:auto; color:#7986cb; font-size:0.75rem;">{ts}</span>
        </div>
        <div style="background:rgba(0,0,0,0.2); border-radius:10px; padding:12px; margin-bottom:12px;
            font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#e8eaf6; line-height:1.7;">
            🔴 MEDISYNTH LIVE EMERGENCY<br><br>
            Health Score: <strong style="color:#ff4757;">{alert.health_score:.0f}/100</strong><br>
            Heart Rate: <strong>{alert.heart_rate:.0f} bpm</strong><br>
            SpO₂: <strong>{alert.spo2:.1f}%</strong><br>
            Risk: <strong style="color:#ff4757;">{alert.risk_level.upper()}</strong><br><br>
            {loc_html}
        </div>
        <div style="font-size:0.7rem; font-weight:600; color:#7986cb; text-transform:uppercase;
            letter-spacing:1px; margin-bottom:6px;">CONTACTS NOTIFIED</div>
        {contacts_html}
    </div>
    """)


# ──────────────────────────── Business Model Panel ───────────────────────────

def render_business_model():
    """Render the business model / pricing panel."""
    _html("""
    <div class="glass-card" style="border-color:rgba(0,212,170,0.15);">
        <div class="section-header">💰 BUSINESS MODEL</div>

        <div style="display:flex; gap:10px; flex-wrap:wrap;">

            <div style="flex:1; min-width:140px; background:rgba(0,212,170,0.06);
                border:1px solid rgba(0,212,170,0.15); border-radius:12px; padding:14px;">
                <div style="color:#00d4aa; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    👤 Consumer Plan
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">$9.99<span style="font-size:0.7rem; color:#7986cb;">/mo</span></div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Real-time monitoring<br>
                    AI health score<br>
                    Emergency alerts<br>
                    Personal baseline
                </div>
            </div>

            <div style="flex:1; min-width:140px; background:rgba(124,58,237,0.06);
                border:1px solid rgba(124,58,237,0.15); border-radius:12px; padding:14px;
                position:relative; overflow:hidden;">
                <div style="position:absolute; top:8px; right:8px; background:#7c3aed;
                    color:white; font-size:0.55rem; padding:2px 6px; border-radius:4px;
                    font-weight:700;">POPULAR</div>
                <div style="color:#a78bfa; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    🏗️ API Access
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">$499<span style="font-size:0.7rem; color:#7986cb;">/mo</span></div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Wearable SDK integration<br>
                    Bulk synthetic data<br>
                    Custom AI models<br>
                    10K API calls/mo
                </div>
            </div>

            <div style="flex:1; min-width:140px; background:rgba(255,179,71,0.06);
                border:1px solid rgba(255,179,71,0.15); border-radius:12px; padding:14px;">
                <div style="color:#ffb347; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    🏥 Hospital License
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">Custom</div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Multi-patient dashboard<br>
                    EHR integration<br>
                    Clinical analytics<br>
                    Dedicated support
                </div>
            </div>

        </div>
    </div>
    """)
