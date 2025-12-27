import json
import os
import threading
import time
from sqlalchemy.orm import Session
from app import models, database

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "knowledge_tags.json")

def export_knowledge_tags():
    """Export all knowledge tags to a JSON file."""
    db = database.SessionLocal()
    try:
        tags = db.query(models.KnowledgeTag).all()
        data = []
        for tag in tags:
            data.append({
                "id": tag.id,
                "teacher_id": tag.teacher_id,
                "subject": tag.subject,
                "chapter": tag.chapter,
                "knowledge_point": tag.knowledge_point
            })
        
        # Ensure directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # print(f"Knowledge tags exported to {CACHE_FILE} at {time.ctime()}")
        
    except Exception as e:
        print(f"Error exporting knowledge tags: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the scheduler to export knowledge tags every 1 minute."""
    def run_job():
        while True:
            export_knowledge_tags()
            time.sleep(60)

    thread = threading.Thread(target=run_job, daemon=True)
    thread.start()
