"""
Medisynth Live – Main Application
AI-Powered Preventive Health Monitoring System

Uses @st.fragment for auto-refreshing dashboard — eliminates duplication by
only re-rendering the dashboard fragment instead of the entire page.
"""

import streamlit as st
import time

import config
from modules.simulation_engine import SimulationEngine
from modules.synthetic_engine import SyntheticEngine
from modules.preprocessing import PreprocessingPipeline
from modules.ai_detection import AIDetectionEngine
from modules.baseline_engine import BaselineEngine
from modules.health_score import HealthScoreEngine
from modules.emergency_system import EmergencySystem
from modules.analytics_engine import AnalyticsEngine
from modules.notification_service import NotificationService
from modules.location_service import request_location, build_maps_link
from modules.sound_alerts import play_alert

from ui.styles import inject_css
from ui.simulation_panel import render_simulation_panel
from ui.patient_view import render_patient_view
from ui.caregiver_view import render_caregiver_view
from ui.doctor_view import render_doctor_view
from ui.components import render_status_banner

# ── Page Config ──
st.set_page_config(
    page_title="Medisynth Live – AI Health Monitoring",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ── Initialize ──
def init_state():
    defaults = {
        "sim_engine": SimulationEngine(),
        "synthetic_engine": SyntheticEngine(),
        "preprocessing": PreprocessingPipeline(),
        "ai_engine": AIDetectionEngine(),
        "baseline_engine": BaselineEngine(),
        "score_engine": HealthScoreEngine(),
        "emergency_system": EmergencySystem(),
        "analytics": AnalyticsEngine(),
        "notification_service": NotificationService(),
        "role": "Patient",
        "last_update": 0.0,
        "tick_count": 0,
        "baseline_started": False,
        "hr_history": [],
        "spo2_history": [],
        "hr_raw_history": [],
        "spo2_raw_history": [],
        "bp_sys_history": [],
        "bp_dia_history": [],
        "rr_history": [],
        "temp_history": [],
        "timestamps": [],
        "processed": None,
        "ai_result": None,
        "score_result": None,
        "deviation": None,
        "sound_muted": False,
        "prev_status": "stable",
        "auto_notified_alert_ts": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "location" not in st.session_state:
        request_location()

init_state()


# ── Sidebar ──
with st.sidebar:
    render_simulation_panel(
        st.session_state.sim_engine,
        st.session_state.synthetic_engine,
        st.session_state.emergency_system,
        st.session_state.notification_service,
    )


# ── Data Processing Function ──
def process_tick():
    """Run one simulation tick: generate → preprocess → analyze → score → alert."""
    now = time.time()
    if (now - st.session_state.last_update) < (config.UPDATE_INTERVAL_S * 0.8):
        return

    st.session_state.last_update = now
    st.session_state.tick_count += 1

    sim = st.session_state.sim_engine
    synth = st.session_state.synthetic_engine
    preproc = st.session_state.preprocessing
    ai = st.session_state.ai_engine
    baseline = st.session_state.baseline_engine
    scorer = st.session_state.score_engine
    emerg = st.session_state.emergency_system
    analytics = st.session_state.analytics
    notif = st.session_state.notification_service

    if sim.mode != analytics.current_mode:
        analytics.record_mode_change(sim.mode)

    if not st.session_state.baseline_started:
        baseline.start_capture()
        st.session_state.baseline_started = True

    # Generate
    reading = None
    if synth.is_active():
        reading = synth.generate_reading(
            base_hr=sim._prev_hr, base_spo2=sim._prev_spo2,
            base_bp_sys=sim._prev_bp_sys, base_bp_dia=sim._prev_bp_dia,
            base_rr=sim._prev_rr, base_temp=sim._prev_temp,
        )
    if not reading:
        reading = sim.generate_reading()

    st.session_state.hr_raw_history.append(reading.heart_rate)
    st.session_state.spo2_raw_history.append(reading.spo2)

    processed = preproc.process(
        reading.heart_rate, reading.spo2,
        reading.bp_systolic, reading.bp_diastolic,
        reading.respiratory_rate, reading.temperature,
    )
    st.session_state.processed = processed

    st.session_state.hr_history.append(processed.clean_hr)
    st.session_state.spo2_history.append(processed.clean_spo2)
    st.session_state.bp_sys_history.append(processed.clean_bp_sys)
    st.session_state.bp_dia_history.append(processed.clean_bp_dia)
    st.session_state.rr_history.append(processed.clean_rr)
    st.session_state.temp_history.append(processed.clean_temp)
    st.session_state.timestamps.append(reading.timestamp)

    max_pts = config.HISTORY_MAX_POINTS
    for key in ["hr_history", "spo2_history", "hr_raw_history", "spo2_raw_history",
                "bp_sys_history", "bp_dia_history", "rr_history", "temp_history", "timestamps"]:
        if len(st.session_state[key]) > max_pts:
            st.session_state[key] = st.session_state[key][-max_pts:]

    if baseline.is_capturing:
        baseline.add_sample(processed.clean_hr, processed.clean_spo2)
    st.session_state.deviation = baseline.compute_deviation(processed.clean_hr, processed.clean_spo2)

    bl_hr = baseline.baseline.hr_mean if baseline.has_baseline() else None
    bl_spo2 = baseline.baseline.spo2_mean if baseline.has_baseline() else None

    ai_result = ai.analyze(
        processed.clean_hr, processed.clean_spo2,
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        baseline_hr=bl_hr, baseline_spo2=bl_spo2,
        confidence=processed.confidence,
    )
    st.session_state.ai_result = ai_result

    score_result = scorer.compute(
        processed.clean_hr, processed.clean_spo2,
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        baseline_hr=bl_hr, baseline_spo2=bl_spo2,
        confidence=processed.confidence,
    )
    st.session_state.score_result = score_result

    analytics.record_reading(
        processed.clean_hr, processed.clean_spo2,
        processed.clean_bp_sys, processed.clean_bp_dia,
        processed.clean_rr, processed.clean_temp,
        score_result.score,
    )
    for det in ai_result.detections:
        analytics.record_detection(det.condition, det.severity, det.evidence[0] if det.evidence else "")

    # AUTO-EMERGENCY
    if emerg.should_trigger_alert(score_result.score, ai_result.overall_status):
        loc = st.session_state.get("location")
        alert = emerg.trigger_alert(
            score_result.score, processed.clean_hr, processed.clean_spo2,
            ai_result.overall_status, location=loc,
        )
        analytics.record_alert(score_result.score)
        maps_link = build_maps_link(loc["lat"], loc["lng"]) if loc and loc.get("lat") else alert.google_maps_link
        emerg.notify_contacts()
        if emerg.contacts and (now - st.session_state.auto_notified_alert_ts > 60):
            notif.send_to_all_contacts_async(emerg.contacts, alert.message, maps_link)
            st.session_state.auto_notified_alert_ts = now
        emerg.confirm_alert()

    if ai_result.overall_status != st.session_state.prev_status:
        if not st.session_state.sound_muted:
            if ai_result.overall_status == "critical":
                play_alert("critical")
            elif ai_result.overall_status == "monitoring":
                play_alert("warning")
        st.session_state.prev_status = ai_result.overall_status


# ── Auto-refreshing Dashboard Fragment ──
@st.fragment(run_every=1.0)
def dashboard_fragment():
    """This fragment auto-reruns every 1s, re-rendering ONLY itself — not the full page."""
    # Process new data
    process_tick()

    # Status
    overall = st.session_state.ai_result.overall_status if st.session_state.ai_result else "stable"
    render_status_banner(overall)

    # Title bar
    st.html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div>
            <span style="font-size:1.4rem; font-weight:800; color:#e8eaf6;">Medisynth Live</span>
            <span style="font-size:0.8rem; color:#7986cb; margin-left:12px;">{st.session_state.role} Dashboard</span>
        </div>
        <div style="font-size:0.75rem; color:#4a5568;">
            Tick #{st.session_state.tick_count} • Mode: {st.session_state.sim_engine.mode.upper()}
        </div>
    </div>
    """)

    # Baseline progress
    if st.session_state.baseline_engine.is_capturing:
        p = st.session_state.baseline_engine.get_capture_progress()
        st.html(f"""
        <div style="background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.2);
            border-radius:10px; padding:8px 16px; margin-bottom:12px; font-size:0.8rem; color:#00d4aa;">
            ⏳ Baseline... {p*100:.0f}%
            <div style="width:100%; height:3px; background:rgba(255,255,255,0.06); border-radius:2px; margin-top:4px;">
                <div style="width:{p*100}%; height:100%; background:#00d4aa; border-radius:2px;"></div>
            </div>
        </div>
        """)

    # Build state
    view_state = {
        "score_result": st.session_state.get("score_result"),
        "ai_result": st.session_state.get("ai_result"),
        "processed": st.session_state.get("processed"),
        "baseline_engine": st.session_state.baseline_engine,
        "deviation": st.session_state.get("deviation"),
        "emergency_system": st.session_state.emergency_system,
        "analytics": st.session_state.analytics,
        "notification_service": st.session_state.notification_service,
        "hr_history": list(st.session_state.hr_history),
        "spo2_history": list(st.session_state.spo2_history),
        "hr_raw_history": list(st.session_state.hr_raw_history),
        "spo2_raw_history": list(st.session_state.spo2_raw_history),
        "bp_sys_history": list(st.session_state.bp_sys_history),
        "bp_dia_history": list(st.session_state.bp_dia_history),
        "rr_history": list(st.session_state.rr_history),
        "temp_history": list(st.session_state.temp_history),
        "mode": st.session_state.sim_engine.mode,
        "synthetic_engine": st.session_state.synthetic_engine,
        "location": st.session_state.get("location"),
    }

    # Render the correct view
    role = st.session_state.role
    if role == "Patient":
        render_patient_view(view_state)
    elif role == "Caregiver":
        render_caregiver_view(view_state)
    elif role == "Doctor":
        render_doctor_view(view_state)

    # ── Browser Notifications (JavaScript) ──
    notif = st.session_state.notification_service
    browser_alerts = notif.get_pending_browser_alerts()
    for alert in browser_alerts:
        title = alert["title"].replace("'", "\\'").replace('"', '\\"')
        body = alert["body"].replace("'", "\\'").replace('"', '\\"')
        st.html(f"""
        <script>
        (function() {{
            if ('Notification' in window) {{
                if (Notification.permission === 'granted') {{
                    new Notification('{title}', {{
                        body: '{body}',
                        icon: '🚨',
                        requireInteraction: true
                    }});
                }} else if (Notification.permission !== 'denied') {{
                    Notification.requestPermission().then(function(p) {{
                        if (p === 'granted') {{
                            new Notification('{title}', {{body: '{body}'}});
                        }}
                    }});
                }}
            }}
        }})();
        </script>
        """)

    # ── WhatsApp Compose Links ──
    wa_links = notif.get_pending_whatsapp_links()
    if wa_links:
        st.html("""
        <div style="background:rgba(37,211,102,0.08); border:1px solid rgba(37,211,102,0.3);
            border-radius:12px; padding:12px; margin:8px 0;">
            <div style="color:#25d366; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                💬 Quick WhatsApp Alert (tap to send)
            </div>
        """)
        for link in wa_links:
            st.html(f"""
            <a href="{link}" target="_blank" style="display:inline-block; background:#25d366;
                color:white; padding:8px 16px; border-radius:8px; text-decoration:none;
                font-weight:600; font-size:0.8rem; margin:4px 4px 4px 0;">
                📲 Send via WhatsApp
            </a>
            """)
        st.html("</div>")


# Run the fragment
dashboard_fragment()

