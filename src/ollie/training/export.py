import json
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from ollie.storage.models import Conversation
from ollie.storage.database import DB_URL

def export_daily_conversations(output_file: str = "/data/training/daily_data.jsonl"):
    """Export conversations from the last 24 hours to JSONL."""
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Filter for last 24 hours
    since = datetime.utcnow() - timedelta(days=1)
    
    # Get conversations
    # We want pairs of User -> Ollie
    # This is tricky if they are just a stream. 
    # We'll look for sessions and reconstruct the dialogue.
    
    stm = select(Conversation).where(Conversation.timestamp >= since).order_by(Conversation.timestamp)
    conversations = session.scalars(stm).all()
    
    # Group by session
    sessions = {}
    for c in conversations:
        if c.session_id not in sessions:
            sessions[c.session_id] = []
        sessions[c.session_id].append(c)
        
    training_data = []
    
    for session_id, chats in sessions.items():
        # Create instruction/input/output format or ChatML
        # Let's assume standard chat format: [{"role": "user", ...}, {"role": "assistant", ...}]
        
        # We iterate and pair them up
        history = []
        for i in range(len(chats)):
            msg = chats[i]
            role = "user" if msg.speaker == "User" else "assistant"
            
            # If we have a user message followed by an assistant message, that's a training pair
            # But generally for chat fine-tuning we feed the whole history
            
            history.append({"role": role, "content": msg.transcript})
            
        if history:
            training_data.append({"messages": history})
            
    # Ensure dir exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        for entry in training_data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Exported {len(training_data)} sessions to {output_file}")

if __name__ == "__main__":
    export_daily_conversations()
