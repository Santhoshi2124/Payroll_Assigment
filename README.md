# Payroll Management System (MVP) — Santoshi

A minimal Payroll Management System (FastAPI backend + React (Vite) frontend) created for assignment submission.
The repository contains Docker support and a simple seeded demo user so evaluators can inspect functionality quickly.

---

## Project structure

```
/frontend    # React (Vite) frontend
/backend     # FastAPI backend (SQLite)
README.md
docker-compose.yml
Assignment E – Payroll Management System.pdf
```

## Seeded demo user (for evaluation)
- **Email:** hire-me@anshumat.org
- **Password:** HireMe@2025!
- **Role:** admin

> The seeded user is created automatically on backend startup using the password hash. Use these credentials to login and inspect admin-only endpoints like salary slip creation and expense approval.

---

## Quick setup (for reviewers who want to run locally)

### Option A — Using Docker (recommended for evaluators)
1. Make sure Docker and docker-compose are installed.
2. From project root, run:
```bash
docker-compose build
docker-compose up -d
```
3. Backend API docs: `http://localhost:8000/docs`  
   Frontend (served by nginx): `http://localhost:5173`

> Backend uses a named Docker volume `backend_db` to persist the SQLite database file.

### Option B — Run locally without Docker (developer)
**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
**Frontend** (requires Node.js):
```bash
cd frontend
npm install
npm run dev
```

---

## Tech stack and justification

**Backend — FastAPI (Python)**  
- FastAPI provides fast development, built-in OpenAPI docs, and async support. It's ideal for quickly building REST APIs for assignments and prototypes. Using SQLite keeps the demo portable for evaluators.

**Frontend — React (Vite)**  
- React is widely used and Vite offers a fast development experience with modern bundling. The frontend is a minimal scaffold demonstrating login flow and can be extended for full UI features.

**Containerization — Docker + Docker Compose**  
- Including Dockerfiles and `docker-compose.yml` demonstrates readiness for production-like deployment and makes evaluation easier (single command to bring up services).

**Why these choices for the assignment?**  
- They balance fast development, readability, portability, and common industry practices. FastAPI + React is a standard modern stack suitable for a small to mid-sized web app; Docker ensures reproducible environments for evaluators.

---

## Notes / Limitations
- The project uses SQLite for simplicity; in a production environment switch to PostgreSQL or MySQL and use secure environment variables for secrets.
- SECRET_KEY in the demo should be changed in real deployments; the docker-compose includes a placeholder and README suggests changing it.
- This is an MVP targeting functionality required by the assignment (auth, salary slips, expense submission/approval).

---

## How to push to GitHub (recommended steps for submission)

1. Create a new repository on GitHub (e.g., `Payroll_Management_System_Assignment`).
2. From the project root locally:
```bash
git init
git add .
git commit -m "Initial commit - Payroll Management System MVP"
git branch -M main
git remote add origin https://github.com/<your-username>/Payroll_Management_System_Assignment.git
git push -u origin main
```
3. Make sure `README.md`, `docker-compose.yml`, and both `frontend/` and `backend/` folders are visible in the repo root — this matches the evaluators' requested structure.

---

If you'd like, I can also:
- Create a `DEPLOY.md` or `SUBMISSION_NOTE.txt` describing what evaluators should check.
- Create a short `CHANGELOG.md` listing files added specifically for the assignment.
- Prepare the exact git commands (with your GitHub repo URL inserted) so you can copy-paste them.

