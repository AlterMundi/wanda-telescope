# Wanda Frontend (Next.js)

This folder hosts the React UI for WANDA, backed by the Flask API that lives in the repository root.

## Prerequisites

- Node.js 20+
- Python backend (`python main.py`) running from the project root

## Environment Variables

Copy the sample file that matches your scenario:

```bash
cp env.local.sample .env.local         # development
cp env.production.sample .env.production   # production build
```

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Base URL for REST requests (defaults to `/api`) |
| `NEXT_PUBLIC_WS_URL` | Base URL for Socket.IO (empty means same origin) |

## Development Workflow

Start Flask in one terminal, Next.js in another:

```bash
# Terminal 1
cd ..
source venv/bin/activate
python main.py

# Terminal 2
npm install
npm run dev
```

Next.js rewrites in `next.config.mjs` forward `/api/*`, `/video_feed`, and `/socket.io/*` to the Flask server.

## Testing

```bash
npm test
```

Uses Vitest and Testing Library to cover the UI components.

## Production Build

```bash
npm run build
npm start
```

See `NEXTJS_INTEGRATION_PLAN.md` in the repository root for systemd + Nginx configuration guidance.

