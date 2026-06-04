---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3044022055483e7b120eda8ec6df9bfd12646aaa21d9238d1b763c0fb131bac88171c7ab02201b0dc32be2e155da7baadfa3707a1574eb21b63bd25bb5adcdb97c102174df64
    ReservedCode2: 3045022100c230a1a6e15cbffd3a18839d9f0dc9084ec19bf94bfa0d7cc19607703e1241e502207e30498916378bcae0af994a9ad8edaa5c1c3111c5d730ea11a90cce68643991
---

# FinAlert Backend - Windows Setup

## Prerequisites

1. **Python 3.12** - Download from https://www.python.org/downloads/
2. **Node.js 18+** - Download from https://nodejs.org/

## Step 1: Install Cloudflare Tunnel (Recommended)

Cloudflare Tunnel is secure and doesn't require an account.

### Option A: Winget (Recommended)
```powershell
winget install Cloudflare.cloudflared
```

### Option B: Manual Download
1. Go to https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Download Windows installer (.msi)
3. Run the installer

## Step 2: Configure Environment Variables

Create a `.env` file in `C:\workspace\finalert-backend\`:
```env
newsapi_key=your_newsapi_key_here
serpapi_key=your_serpapi_key_here
```

## Step 3: Run the Backend

**Terminal 1 - Backend Server:**
```powershell
cd C:\workspace\finalert-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Cloudflare Tunnel:**
```powershell
cloudflared tunnel --url http://localhost:8000
```

When Cloudflare starts, you'll see:
```
Your quick Tunnel has been created! Visit it at:
https://xxxx-xxxx-xxxx.trycloudflare.com
```

## Step 4: Update Frontend

1. Copy the Cloudflare URL
2. Edit `C:\workspace\finalert-dashboard\src\config\api.config.ts`:
```typescript
export const API_BASE_URL = 'https://xxxx-xxxx-xxxx.trycloudflare.com';
```
3. Rebuild: `npm run build`
4. Deploy the `dist` folder

## Quick Start Script

Double-click `run_with_cloudflare.bat` to start both services.

## Troubleshooting

**cloudflared not found:**
- Run `winget install Cloudflare.cloudflared`
- Or restart your terminal after installation

**Port 8000 in use:**
- Change port: `python -m uvicorn app.main:app --port 8001`
- Update tunnel: `cloudflared tunnel --url http://localhost:8001`

**Python venv issues:**
```powershell
python -m venv venv --clear
venv\Scripts\activate
pip install -r requirements.txt
```
