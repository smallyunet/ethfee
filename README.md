# ethfee

A simple full-stack tool to display the latest Ethereum gas fee. Includes a web interface and future support for automatic posting to Telegram and X (Twitter).

## 🧱 Tech Stack

- **Frontend**: Next.js (App Router) + Tailwind CSS
- **Backend**: FastAPI + web3.py + APScheduler
- **Deployment**: Docker Compose

---

## 🚀 Quick Start

### Clone the project

```bash
git clone https://github.com/smallyunet/ethfee.git
cd ethfee
```

### Set up environment variables

Create a `.env` file in the root directory with the following content:

```env
# Backend
ETHERSCAN_API_KEY=your_etherscan_key
TELEGRAM_TOKEN=your_telegram_bot_token
TWITTER_API_KEY=your_x_api_key

# Frontend
NEXT_PUBLIC_API_URL=http://backend:8000
```

---

### Start the project

```bash
docker compose up --build
```

- Frontend available at: http://localhost:3000  
- Backend API available at: http://localhost:8000/gas

---

## 📦 Project Structure

```plaintext
ethfee/
├── backend/      # FastAPI backend service
├── frontend/     # Next.js frontend app
├── .env          # Environment variables
├── docker-compose.yml
```

---

## ✅ TODO

- [ ] Display gas fee history (charts)
- [ ] Telegram bot integration
- [ ] X (Twitter) posting automation
- [ ] UI improvements
