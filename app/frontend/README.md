# SCANX Frontend

Next.js 15 + TypeScript + Tailwind UI for the SCANX demo. For full project details, see the root `README.md`.

## Setup

```bash
npm install
npm run dev
```

Environment:
- `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`)

Key paths:
- `app/page.tsx` → renders `ScanPage`
- `app/components/ScanPage.tsx` → upload/camera + intent UI
- `app/lib/api.ts` → calls FastAPI backend

Styling: Tailwind (see `app/globals.css`). Icon: `app/icon.svg`.
