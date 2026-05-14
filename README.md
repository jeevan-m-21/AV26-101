# 🫀 Medisynth Live – AI-Powered Preventive Health Monitoring System

A real-time, AI-driven healthcare monitoring dashboard with explainable AI, personalized baselines, health scoring, and emergency response capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 🎮 Demo Flow

1. **Launch** → Dashboard starts in Normal mode, baseline capture begins
2. **Wait 30s** → Personal baseline is established
3. **Click "Stress"** → Watch HR gradually rise, health score dips
4. **Click "Critical"** → HR spikes, SpO₂ drops, AI reasoning activates
5. **Health Score drops** → Emergency alert triggers automatically
6. **Add contacts** → Emergency contacts receive simulated notifications
7. **Click "Normal"** → Watch recovery in real-time

## 🏗️ Architecture

| Module | Purpose |
|--------|---------|
| `simulation_engine.py` | Real-time vital sign generation (HR, SpO₂) |
| `synthetic_engine.py` | Rare medical scenario generator |
| `preprocessing.py` | Noise filtering, smoothing, confidence scoring |
| `ai_detection.py` | Explainable AI detection (tachycardia, hypoxia, trends) |
| `baseline_engine.py` | Personalized baseline capture & deviation tracking |
| `health_score.py` | Weighted health score computation (0-100) |
| `emergency_system.py` | 3-step emergency alert flow |

## 👥 Role-Based Views

- **Patient**: Clean vitals, health score, AI insights
- **Caregiver**: Alert feed, patient status, location sharing
- **Doctor**: Detailed trends, raw vs processed data, full AI analysis

## 📊 Health Score

Weighted scoring system (0-100):
- Heart Rate condition: 40%
- SpO₂ condition: 30%
- Baseline deviation: 20%
- Data confidence: 10%

## 🔧 Tech Stack

- **Python** + **Streamlit** (dashboard framework)
- **Plotly** (interactive charts)
- **NumPy** (signal processing)
