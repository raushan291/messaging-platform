# Messaging-platform

## Environment Setup

After cloning the repository, you must create environment variables for the frontend.

Create the file:

```bash
cd frontend/
cp .env.example .env.local
```

If `.env.example` does not exist, create `.env.local` manually and add:

```env
NEXT_PUBLIC_AUTH_API=http://localhost:8001/api/v1
NEXT_PUBLIC_MESSAGING_API=http://localhost:8002/api/v1
NEXT_PUBLIC_WS_API=ws://localhost:8002/api/v1
```

---

## Start Auth Service

```bash
cd backend/services/auth-service/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Auth service will run at:
http://localhost:8001

---

## Start Messaging Service

```bash
cd backend/services/messaging-service/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

Messaging service will run at:
http://localhost:8002

---

## Start Frontend

```bash
cd frontend/
# If npm dependencies are not installed yet, install them first:
npm install
# Then start the development server:
npm run dev
```

Frontend will run at:
http://localhost:3000  
