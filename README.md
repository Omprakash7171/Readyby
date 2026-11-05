# ReadyBy

Order-ahead coffee for pickup. A customer tells ReadyBy where they are heading
and when they will arrive; the café sees that arrival time on every ticket, so
prep starts when it should and nothing is delivered.

The app is two processes: a Django API that owns all the truth (prices,
availability, timings, order status) and a Next.js client that renders it.

- Pickup only. No delivery, no GPS, no card collection — customers pay at the
  counter.
- Everything a customer sees about price, timing, distance and status comes from
  the API. The client never invents a figure.
- Fictional demo cafés are flagged `is_demo` and hidden unless
  `SHOW_DEMO_CAFES=true`.

## Prerequisites

- Python 3.12+
- Node.js 20+

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env      # then edit DEBUG=true, SHOW_DEMO_CAFES=true
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

`seed_demo_data` creates five destinations, five cafés with menus, and two demo
accounts. It is safe to re-run; pass `--reset` to delete existing demo rows
first. Set `DEMO_SEED_PASSWORD` to choose the demo passwords.

| Account | Email | Password |
| --- | --- | --- |
| Customer | `customer@readyby.demo` | `readyby-demo-2026` |
| Café owner | `merchant@readyby.demo` | `readyby-demo-2026` |

The merchant account owns the `bean-and-brew` café, so that is the one with
orders on its board. New accounts registered through the UI are always
customers.

## Frontend

```powershell
Copy-Item .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to 127.0.0.1:8000
npm install
npm run dev
```

Open <http://localhost:3000>. Sign in as the merchant to reach `/merchant`,
which is the pickup board: accept, prepare, mark ready, hand over.

## Checks

```powershell
cd backend && .\.venv\Scripts\python.exe manage.py test   # 158 tests
cd .. && npm run lint && npx tsc --noEmit && npm run build
```

Generate the OpenAPI schema with
`python manage.py spectacular --file schema.yml` (it is gitignored).

## API

Token auth: `Authorization: Token <key>`, issued by `POST /api/auth/login/`.

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/` |
| Catalogue | `GET /api/destinations/`, `/api/cafes/`, `/api/cafes/<slug>/`, `/api/cafes/<slug>/menu/` |
| Customer orders | `POST /api/orders/new/`, `GET /api/orders/`, `GET /api/orders/<public_id>/`, `GET /api/orders/<public_id>/status/`, `POST /api/orders/<public_id>/cancel/` |
| Café board | `GET /api/merchant/cafe/`, `GET /api/merchant/orders/`, `GET /api/merchant/orders/summary/`, `PATCH /api/merchant/orders/<public_id>/status/`, `POST /api/merchant/orders/<public_id>/next-action/` |

`GET /api/cafes/` takes `destination` and `arrival_time`, and returns cafés
ranked by walking distance with an open/closed state, `unavailable_reason`, and
the server-computed plan for that arrival time. Order creation is idempotent
through `idempotency_key`.

Orders move `PLACED → ACCEPTED → PREPARING → READY → COLLECTED`, and may be
cancelled by either side only while `PLACED` or `ACCEPTED`.

## How the timing works

For an arrival at 10:30 with an 8 minute prep time, the café starts at 10:22 and
the order is ready at 10:30. A two-minute buffer applies to how soon an arrival
can be booked, not to the visible start time: the customer always sees the same
arrival and start times the café does.