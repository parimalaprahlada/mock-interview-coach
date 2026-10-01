from pathlib import Path
import os
from langchain_community.chat_message_histories import SQLChatMessageHistory

## path for sqlite file
DATA_DIR = Path("/data") if os.getenv("SPACE_ID") else Path(__file__).parent / "data"

DB_PATH = DATA_DIR / "interview_history.db"
DATA_DIR.mkdir(exist_ok=True)

#check user history
def get_session_history(session_id: str):
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=f"sqlite:///{DB_PATH.as_posix()}",
    )