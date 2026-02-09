# 🥾 Dr. Martens AI Customer Support System

An intelligent, full-stack customer support platform powered by **Anthropic Claude** that autonomously handles customer inquiries, processes refunds, initiates repairs, and escalates complex issues.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange?style=flat-square)

---

## ✨ Features

### 🤖 Agentic AI (Powered by Claude)
- **Autonomous Decision Making** - Claude analyzes customer context and takes appropriate actions
- **Tool Use** - 6 integrated tools for order lookup, refunds, repairs, exchanges, escalations, and appointments
- **Context-Aware Responses** - Personalized replies based on customer history, sentiment, and issue type
- **Empathetic Communication** - Extra care for frustrated customers (1-star reviews, negative sentiment)

### 🔧 Autonomous Actions
| Action | Trigger | What Happens |
|--------|---------|--------------|
| **Refund** | Customer wants money back | Processes refund + 15% discount code |
| **Repair** | Product broken/damaged | Initiates For Life warranty repair |
| **Exchange** | Wrong size/fit issues | Creates free exchange with expedited shipping |
| **Escalate** | Complex issues, angry customers | Routes to senior support with full context |
| **Appointment** | In-store fitting request | Books store appointment with specialist |

### 📊 Real-Time Analytics
- Auto-resolution rate tracking
- Average handle time metrics
- Escalation rate monitoring
- Issue category breakdown
- Customer sentiment analysis

### 🎨 Professional UI
- Dr. Martens branded design (yellow/black theme)
- Responsive chat interface
- Customer context display
- Quick action buttons
- Suggestion chips for guided conversations

---

## 🏗️ Architecture

```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐
│                 │ ◄────────────────► │                 │
│  React Frontend │                    │  Flask Backend  │
│  (Port 3000)    │                    │  (Port 5000)    │
│                 │                    │                 │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │  Anthropic API  │
                                       │  (Claude)       │
                                       └────────┬────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │  Agent Tools    │
                                       │  - lookup_order │
                                       │  - refund       │
                                       │  - repair       │
                                       │  - exchange     │
                                       │  - escalate     │
                                       │  - appointment  │
                                       └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API Key ([Get one here](https://console.anthropic.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/naazima/drmartens-ai-customer-support.git
cd drmartens-ai-customer-support
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
python app.py
```

### 3. Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 4. Open the App
Visit `http://localhost:3000` in your browser.

### 5. Test with Real Data
Try these order numbers from the scraped dataset:

| Order | Customer | Issue |
|-------|----------|-------|
| `DM24382608` | Kim B. | Comfort/Stiffness |
| `DM24136267` | Bridgette C. | Strap broke |
| `DM24169685` | TZ | Quality complaint |
| `DM24140207` | Marissa | Sizing issue |

---

## 📁 Project Structure

```
drmartens-ai-customer-support/
├── backend/
│   ├── app.py                              # Flask API + Claude Agent
│   ├── requirements.txt                    # Python dependencies
│   ├── .env.example                        # Environment template
│   └── dr_martens_training_dataset_50.csv  # Real scraped customer data
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                         # Main React component
│   │   ├── main.jsx                        # Entry point
│   │   └── index.css                       # Tailwind styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── .gitignore
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + config status |
| GET | `/api/customers` | List all customer order numbers |
| GET | `/api/customer/<order>` | Get customer details by order |
| POST | `/api/chat` | Main chat endpoint (Claude-powered) |
| POST | `/api/action/<type>` | Execute specific action |
| GET | `/api/kpis` | Get dashboard metrics |

### Example Chat Request
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My order DM24136267 has a broken strap"}'
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **AI/LLM** | Anthropic Claude (claude-sonnet-4-20250514) |
| **Backend** | Python, Flask, Flask-CORS |
| **Frontend** | React 18, Vite, Tailwind CSS |
| **Icons** | Lucide React |
| **Data** | Pandas, CSV (scraped from Yotpo API) |

---

## 📈 Key Metrics

| Metric | Value |
|--------|-------|
| Auto-Resolution Rate | ~70% |
| Avg Handle Time | 2.3 seconds |
| Escalation Rate | ~30% |
| Issues Covered | Repair, Sizing, Refund, Quality, Service |

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Yes |
| `PORT` | Backend port (default: 5000) | No |

---

## 🚢 Deployment

### Backend (Render)
1. Connect your GitHub repo to [Render](https://render.com)
2. Create a new **Web Service**
3. Set root directory: `backend`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn app:app`
6. Add environment variable: `ANTHROPIC_API_KEY`

### Frontend (Vercel)
1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Set root directory: `frontend`
3. Framework preset: Vite
4. Update `API_BASE` in App.jsx to your Render backend URL

---

## 🎯 Use Cases

- **Customer Service Automation** - Handle common inquiries without human intervention
- **Sentiment-Based Routing** - Automatically escalate angry customers
- **Warranty Processing** - Streamline repair requests under "For Life" program
- **Size Exchange Management** - Quick resolution for fit issues
- **Performance Analytics** - Track and improve support metrics

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 👩‍💻 Author

**Afreen Naaz**
- GitHub: [@naazima](https://github.com/naazima)

---

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for Claude API
- [Dr. Martens](https://drmartens.com) for inspiration
- [Yotpo](https://yotpo.com) for review data API

---

*Built with ❤️ using Claude AI*
