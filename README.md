# NETGUARD IDS

**AI-powered Intrusion Detection System** built with XGBoost, FastAPI, React, Scapy, and Telegram notifications.

Monitors live network traffic in real-time, classifies flows as NORMAL or MALICIOUS using a machine-learning model trained on the CIC-IDS2017 dataset, and sends instant alerts to Telegram.

```
┌─────────────────────────────────────────────────────────────────┐
│                        NETGUARD IDS                             │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────────┐              │
│   │  Scapy   │───▶│  Flow    │───▶│   XGBoost    │              │
│   │ Sniffer  │    │ Tracker  │    │  Classifier  │              │
│   └──────────┘    └──────────┘    └──────┬───────┘              │
│        │                                 │                      │
│        │           ┌─────────────────────┼──────────┐           │
│        │           │                     ▼          │           │
│        │     ┌─────┴─────┐    ┌──────────────┐     │           │
│        │     │ WebSocket │    │   Telegram   │     │           │
│        │     │ Broadcast │    │    Alerts    │     │           │
│        │     └─────┬─────┘    └──────────────┘     │           │
│        │           │                                │           │
│        │           ▼                                │           │
│   ┌────┴───────────────────┐    ┌──────────────┐   │           │
│   │     FastAPI Backend    │───▶│   SQLite DB  │   │           │
│   └────────────┬───────────┘    └──────────────┘   │           │
│                │                                    │           │
│                ▼                                    │           │
│   ┌────────────────────────┐                        │           │
│   │   React Dashboard      │                        │           │
│   │   (Vite + Recharts)    │                        │           │
│   └────────────────────────┘                        │           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Root / sudo access | Required for Scapy raw sockets |

---

## 1. Clone & Setup

```bash
cd ids-system
```

---

## 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Dataset: CIC-IDS2017

1. Download the CIC-IDS2017 dataset from:  
   **https://www.unb.ca/cic/datasets/ids-2017.html**

2. Place **all CSV files** into the `data/` directory:

```
data/
├── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
├── Friday-WorkingHours-Morning.pcap_ISCX.csv
├── Monday-WorkingHours.pcap_ISCX.csv
├── Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
├── Tuesday-WorkingHours.pcap_ISCX.csv
└── Wednesday-workingHours.pcap_ISCX.csv
```

---

## 4. Train the Model

```bash
python -m backend.ml.train
```

This will:
- Load all CSVs from `data/`
- Clean NaN/Infinity rows
- Train an XGBoost classifier (200 estimators, max_depth=6)
- Save the model to `models/ids_model.pkl`
- Save feature columns to `models/feature_columns.pkl`
- Print accuracy, precision, recall, F1, and confusion matrix

**Training takes 10–20 minutes** depending on your hardware.

---

## 5. Telegram Setup (Optional)

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts to create a bot
3. Copy the **bot token**
4. Send a message to your new bot
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find your **chat_id** in the response JSON
7. Update `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIjKlMnOpQrStUvWxYz
TELEGRAM_CHAT_ID=987654321
```

If not configured, the IDS will still work — Telegram alerts will simply be skipped.

---

## 6. Run the Backend

```bash
sudo uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note:** `sudo` is required because Scapy uses raw sockets for packet capture.

---

## 7. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 8. Use

1. Open **http://localhost:5173**
2. Select your network interface from the dropdown
3. Click **START CAPTURE**
4. Watch real-time flows, classifications, and the traffic chart

---

## Project Structure

```
ids-system/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment config
│   ├── capture/
│   │   ├── packet_sniffer.py # Scapy real-time sniffer
│   │   └── flow_tracker.py   # Flow tracker re-export
│   ├── ml/
│   │   ├── feature_extractor.py  # CIC-IDS2017 feature extraction
│   │   ├── train.py              # XGBoost training pipeline
│   │   └── predict.py            # Inference singleton
│   ├── api/
│   │   ├── routes.py         # REST + WebSocket endpoints
│   │   └── schemas.py        # Pydantic models
│   ├── notifications/
│   │   └── telegram_bot.py   # Telegram alert system
│   └── db/
│       ├── database.py       # SQLAlchemy setup
│       └── models.py         # Alert ORM model
├── frontend/
│   ├── src/
│   │   ├── components/       # React UI components
│   │   ├── hooks/            # WebSocket hook
│   │   └── api/              # Axios client
│   └── ...config files
├── data/                     # CIC-IDS2017 CSVs (user-provided)
├── models/                   # Trained model artifacts
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/status` | System status |
| GET | `/api/interfaces` | List network interfaces |
| POST | `/api/capture/start` | Start packet capture |
| POST | `/api/capture/stop` | Stop packet capture |
| GET | `/api/alerts` | Paginated alerts (filter, page, limit) |
| GET | `/api/stats` | Aggregate statistics |
| WS | `/ws/live` | Real-time WebSocket feed |

---

## Troubleshooting

### ❌ "Permission denied" from Scapy
Scapy requires root privileges for raw socket access:
```bash
sudo uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### ❌ "Model file not found"
Train the model first:
```bash
python -m backend.ml.train
```

### ❌ "No CSV files found in data/"
Download the CIC-IDS2017 dataset and place the CSV files in the `data/` directory.

### ❌ Network interface not found
List available interfaces:
```bash
python -c "import psutil; print(list(psutil.net_if_addrs().keys()))"
```
On macOS, the main interface is usually `en0`. On Linux, it's `eth0` or `wlan0`. Update `.env` accordingly.

### ❌ WebSocket disconnects
The frontend auto-reconnects with exponential backoff. If the backend is down, you'll see a red "DISCONNECTED" indicator in the dashboard header.

### ❌ Telegram messages not sending
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Make sure you've sent at least one message to your bot first
- Check the backend logs for Telegram API errors

---

## Tech Stack

- **Frontend**: React + Vite + TailwindCSS + Recharts + React Router (Authentication & Routing)
- **Backend**: FastAPI + Python 3.11 + JWT Authentication
- **ML**: XGBoost trained on CIC-IDS2017 dataset
- **Packet Capture**: Scapy (real-time, runs in background thread)
- **Notifications**: Telegram Bot API via httpx
- **Real-time**: WebSocket (FastAPI native)
- **Batch Processing**: Pandas-based PCAP CSV parsing & prediction
- **Database**: SQLite via SQLAlchemy
- **Environment**: python-dotenvse

---

## License

MIT
# ids
# ids
