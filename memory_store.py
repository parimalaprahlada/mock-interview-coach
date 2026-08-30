from pathlib import Path
from langchain_community.chat_message_histories import SQLChatMessageHistory

##path for sqlite file
DATA_DIR = Path(__file__).parent / "data"

DB_PATH = DATA_DIR / "interview_history.db"
DATA_DIR.mkdir(exist_ok=True)

#check user history
def get_session_history(session_id: str):
    ##Reconnects to the same file/session_id for each call , so history persists across restarts instead of just living in the memory
    return SQLChatMessageHistory(
        session_id=session_id, 
        connection=f"sqlite:///{DB_PATH.as_posix()}",
    )

