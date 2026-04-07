from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users

app = FastAPI(title="My API", version="1.0.0")

# CORS — important for React Native!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"status": "ok"}