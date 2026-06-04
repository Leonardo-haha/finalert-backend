---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3046022100985c0584720697842e907432248961556c62e1bba2ddd42e836f44eb1e652989022100a6cf0eea686c5662d50bb8dc7aa1c9d3fdd522cd0996e978b3c987ea2527057c
    ReservedCode2: 3046022100fb21fdb42a0f1e091d5f136336c9b4d01488ad8f6bea1d93a6d2d074dad3713f0221009ac1fdc16c2427ef584b79e6b6768ffc90c00c173d92645ef268f4c6d1442c5e
---

# FinAlert Backend - Windows Setup with Cloudflare Tunnel

## Step 1: Install Cloudflare Tunnel (cloudflared)

### Option A: Winget (Recommended)
```powershell
winget install Cloudflare.cloudflared
```

### Option B: Manual Download
1. Go to https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Download Windows installer
3. Run the installer

## Step 2: Configure Environment Variables

Create or edit `.env` file in `C:\workspace\finalert-backend\`:

```env
newsapi_key=your_newsapi_key_here
serpapi_key=your_serpapi_key_here
```

## Step 3: Run with Cloudflare Tunnel

### Method A: Using the provided batch script

```powershell
cd C:\workspace\finalert-backend
run_with_cloudflare.bat
```

### Method B: Manual commands (run in separate terminals)

**Terminal 1 - Backend:**
```powershell
cd C:\workspace\finalert-backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Cloudflare Tunnel:**
```powershell
cloudflared tunnel --url http://localhost:8000
```

Cloudflare will show a URL like:
```
Your quick Tunnel has been created! Visit it at:
https://random-name.trycloudflare.com
```

## Step 4: Update Frontend URL

1. Copy the Cloudflare URL (e.g., `https://random-name.trycloudflare.com`)

2. Edit `/workspace/finalert-dashboard/src/config/api.config.ts`:
```typescript
export const API_BASE_URL = 'https://random-name.trycloudflare.com';
```

3. Rebuild and redeploy:
```powershell
cd C:\workspace\finalert-dashboard
npm run build
```

Then deploy the `dist` folder again.

## Advantages of Cloudflare Tunnel

- **No account required** - works immediately after install
- **Secure** - uses Cloudflare's