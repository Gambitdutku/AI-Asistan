from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from database import engine, Base, get_db
import models
from agent import get_agent_executor

# modelden tablo oluşturma
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):

   ''' return templates.TemplateResponse("index.html", {"request": request})
   bu kalkmış ben de yeni öğrendim '''
   return templates.TemplateResponse(request, "index.html", {})

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    session_id = payload.session_id
    user_message = payload.message
    executor = get_agent_executor()

    # mesaj geçmişi alıyoruz
    history_records = db.query(models.ChatHistory).filter(models.ChatHistory.session_id == session_id).order_by(
        models.ChatHistory.created_at.asc()).all()

    chat_history = []
    for rec in history_records:
        if rec.role == "human":
            chat_history.append(HumanMessage(content=rec.content))
        else:
            chat_history.append(AIMessage(content=rec.content))

    db.add(models.ChatHistory(session_id=session_id, role="human", content=user_message))
    db.commit()

    try:

        messages = chat_history + [HumanMessage(content=user_message)]
        response = executor.invoke({"messages": messages})
        ai_response = response["messages"][-1].content

        # yanıtları kaydediyoruz
        db.add(models.ChatHistory(session_id=session_id, role="ai", content=ai_response))
        db.commit()
        return {"session_id": session_id, "response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent hatası: {str(e)}")


@app.get("/api/sessions")
async def get_active_sessions(db: Session = Depends(get_db)):
    distinct_sessions = db.query(models.ChatHistory.session_id).distinct().all()
    return [s[0] for s in distinct_sessions]


@app.get("/api/chat/{session_id}")
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    history = db.query(models.ChatHistory).filter(models.ChatHistory.session_id == session_id).order_by(
        models.ChatHistory.created_at.asc()).all()
    return [{"role": h.role, "content": h.content, "timestamp": h.created_at} for h in history]


@app.get("/api/appointments")
async def get_all_appointments(db: Session = Depends(get_db)):
    #ajan kullanmadan randevuları alıyoruz
    appointments = (
        db.query(models.Appointment)
        .order_by(models.Appointment.start_time.asc())
        .all()
    )
    result = []
    for app in appointments:
        result.append({
            "id": app.id,
            "title": app.title,
            "start_time": app.start_time,
            "description": app.description,
            "customer": {
                "id": app.customer.id,
                "name": app.customer.name,
                "email": app.customer.email,
                "phone": app.customer.phone
            } if app.customer else None
        })
    return result
