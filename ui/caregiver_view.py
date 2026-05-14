"""
Medisynth Live – Caregiver Dashboard View
Alerts, patient status, vitals, risk, location, timeline.
"""

import streamlit as st
from ui.components import (
    render_vital_card, render_bp_card, render_health_gauge,
    create_vitals_chart, render_confidence_badge, render_risk_prediction,
    render_event_timeline, render_session_info, render_data_source_label,
    render_emergency_notification,
)


def render_caregiver_view(state: dict):
    """Render the Caregiver dashboard."""
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    mode = state.get("mode", "normal")

    if analytics:
        render_session_info(analytics.session_id, analytics.get_elapsed_str(), analytics.total_readings)
    render_data_source_label(mode)

    # Emergency at top
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        if st.button("✕ Dismiss", key="cg_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    left, right = st.columns([1.3, 1.7])

    with left:
        st.html('<div class="section-header">👤 Patient Status</div>')
        if score_result:
            render_health_gauge(score_result.score, score_result.status_label, score_result.status_color, score_result.status_emoji)

        if processed:
            c1, c2 = st.columns(2)
            with c1:
                render_vital_card("Heart Rate", processed.clean_hr, "bpm", "💓", "#00d4aa", sparkline_data=hr_history[-20:])
            with c2:
                render_vital_card("SpO₂", processed.clean_spo2, "%", "🫁", "#a78bfa", sparkline_data=spo2_history[-20:])
            c3, c4 = st.columns(2)
            with c3:
                render_bp_card(processed.clean_bp_sys, processed.clean_bp_dia, bp_sys_history[-20:])
            with c4:
                render_vital_card("Resp Rate", processed.clean_rr, "br/min", "🌬️", "#38bdf8", sparkline_data=rr_history[-20:])

        # Alert history
        if emergency and emergency.alert_history:
            with st.expander(f"📋 Alert History ({len(emergency.alert_history)})"):
                for alert in reversed(emergency.alert_history[-5:]):
                    import datetime
                    ts = datetime.datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
                    st.html(f'<div style="padding:4px 0; font-size:0.8rem;"><span style="color:#7986cb;">{ts}</span> <span style="color:#ff4757; font-weight:600;">Score: {alert.health_score:.0f}</span></div>')

    with right:
        st.html('<div class="section-header">📊 Live Monitoring</div>')
        if hr_history and spo2_history:
            fig = create_vitals_chart([], hr_history, spo2_history)
            st.plotly_chart(fig, use_container_width=True, key="cg_chart")

        if ai_result and ai_result.risk_prediction:
            render_risk_prediction(ai_result.risk_prediction)

        # Real location during emergencies
        if emergency and emergency.active_alert and location and location.get("lat"):
            maps_link = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"
            city = f"{location.get('city','')} {location.get('region','')}"
            st.html(f"""
            <div class="glass-card">
                <div style="color:#e8eaf6; font-weight:600;">📍 Patient Location</div>
                <div style="color:#7986cb; font-size:0.8rem; margin-top:4px;">
                    {city} ({location['lat']:.4f}, {location['lng']:.4f})
                </div>
                <a href="{maps_link}" target="_blank" style="color:#00d4aa; font-size:0.8rem;">🗺️ Open in Maps</a>
            </div>
            """)

        if analytics:
            render_event_timeline(analytics.timeline, max_events=6)

        if ai_result:
            summary_color = "#ff4757" if ai_result.overall_status == "critical" else "#ffb347" if ai_result.overall_status == "monitoring" else "#00d4aa"
            st.html(f"""
            <div class="glass-card">
                <div class="section-header">🤖 AI Summary</div>
                <div style="color:{summary_color}; font-weight:600; font-size:0.85rem;">{ai_result.summary}</div>
            </div>
            """)
