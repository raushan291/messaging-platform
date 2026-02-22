# Messaging-platform

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
npm run dev
```

Frontend will run at:
http://localhost:3000  
