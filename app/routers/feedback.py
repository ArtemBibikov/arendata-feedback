from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Feedback as FeedbackModel
from app.crud import create_feedback
from app.schemas import FeedbackCreate
from app.services.telegram import send_critical_notification

router = APIRouter()

@router.post("/feedback", summary="Создать отзыв")
async def create_feedback_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        import json
        body = await request.body()
        feedback_data = json.loads(body.decode("utf-8"))
        
        message_text = feedback_data.get("message", "").lower()
        if any(word in message_text for word in ["срочно", "критический", "не работает", "сломалось", "авария", "проблема", "ошибка"]):
            feedback_data["urgency"] = "high"
        else:
            feedback_data["urgency"] = "high"
        
        db_feedback = create_feedback(db=db, feedback=FeedbackCreate(**feedback_data))
        
        if db_feedback.urgency == "high":
            background_tasks.add_task(send_critical_notification, db_feedback)
        
        return db_feedback
    except Exception as e:
        print(f"Error: {e}")
        raise e
