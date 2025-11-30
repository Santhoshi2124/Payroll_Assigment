from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List
import sqlite3
import os

SECRET_KEY = "CHANGE_THIS_SECRET"  # change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="Payroll Management API")

DB_FILE = os.path.join(os.path.dirname(__file__), "payroll.db")

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript(\"\"\"
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        role TEXT NOT NULL -- "admin" or "employee"
    );
    CREATE TABLE IF NOT EXISTS salary_slips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        amount REAL NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        month TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    \"\"\")
    conn.commit()
    # Seed demo admin & employee
    try:
        cur.execute("INSERT INTO users (email, hashed_password, full_name, role) VALUES (?,?,?,?)",
                    ("hire-me@anshumat.org", pwd_context.hash("HireMe@2025!"), "Demo Admin", "admin"))
    except Exception:
        pass
    try:
        cur.execute("INSERT INTO users (email, hashed_password, full_name, role) VALUES (?,?,?,?)",
                    ("employee1@example.com", pwd_context.hash("password123"), "Demo Employee", "employee"))
    except Exception:
        pass
    conn.commit()

@app.on_event("startup")
def startup():
    init_db()

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = None
    role: str = "employee"

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    return row

def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user: return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

def require_admin(user):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

# Auth endpoints
@app.post("/auth/signup", response_model=dict)
def signup(u: UserCreate):
    conn = get_db()
    cur = conn.cursor()
    hashed = get_password_hash(u.password)
    try:
        cur.execute("INSERT INTO users (email, hashed_password, full_name, role) VALUES (?,?,?,?)",
                    (u.email, hashed, u.full_name, u.role))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail="User already exists or invalid input")
    return {"msg":"user created"}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
def me(current_user=Depends(get_current_user)):
    return {"email": current_user["email"], "full_name": current_user["full_name"], "role": current_user["role"]}

# Admin: create & update salary slips
@app.post("/salary-slip")
def create_salary_slip(payload: dict, current_user=Depends(get_current_user)):
    require_admin(current_user)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO salary_slips (user_id, month, amount, notes) VALUES (?,?,?,?)",
                (payload.get("user_id"), payload.get("month"), payload.get("amount"), payload.get("notes")))
    conn.commit()
    return {"msg":"created"}

@app.put("/salary-slip/{sid}")
def update_salary_slip(sid: int, payload: dict, current_user=Depends(get_current_user)):
    require_admin(current_user)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE salary_slips SET month=?, amount=?, notes=? WHERE id=?",
                (payload.get("month"), payload.get("amount"), payload.get("notes"), sid))
    conn.commit()
    return {"msg":"updated"}

# Employee: view own salary slips
@app.get("/salary-slip")
def view_salary_slips(current_user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM salary_slips WHERE user_id = ?", (current_user["id"],))
    rows = [dict(r) for r in cur.fetchall()]
    return rows

# Employee: submit expense, view own expense history
@app.post("/expense")
def submit_expense(payload: dict, current_user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (user_id, amount, description, month) VALUES (?,?,?,?)",
                (current_user["id"], payload.get("amount"), payload.get("description"), payload.get("month")))
    conn.commit()
    return {"msg":"submitted"}

@app.get("/expense")
def view_expenses(current_user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id = ?", (current_user["id"],))
    rows = [dict(r) for r in cur.fetchall()]
    return rows

# Basic admin expense approval
@app.post("/expense/{eid}/approve")
def approve_expense(eid: int, current_user=Depends(get_current_user)):
    require_admin(current_user)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE expenses SET status='approved' WHERE id=?", (eid,))
    conn.commit()
    return {"msg":"approved"}
