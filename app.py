import streamlit as st

from dotenv import load_dotenv
load_dotenv()
from langchain_core.runnables.history import RunnableWithMessageHistory
from chains import interview_chain, feedback_chain
from memory_store import get_session_history

interview_with_memory = RunnableWithMessageHistory(
    interview_chain, 
    get_session_history, 
    input_messages_key="input",
    history_messages_key="history"
)

def format_transcript(session_id: str) -> str:
    history = get_session_history(session_id)
    lines=[]
    for msg in history.messages:
        speaker = "interviewer" if msg.type=="ai" else "Candidate"
        lines.append(f"{speaker}: {msg.content}")
    return "\n".join(lines)

##set tab title and page title using streamlit

st.set_page_config(page_title="AI Mock Interview Coach", page_icon="🎤")
st.title("🎤 AI Mock Interview Coach")

with st.sidebar:
    name = st.text_input("Your name (this is your session ID)")
    role = st.text_input("Role you're interviewing for", placeholder="e.g. AI Engineer")
    start_clicked = st.button("Start / Resume Interview")

if "started" not in st.session_state:
    st.session_state.started = False
if start_clicked and name and role:
    st.session_state.started = True

if not st.session_state.started:
    st.info("Enter your name and role, then click 'Start / Resume Interview")
    st.stop()

#tell langchain which student's session to read/write and checks it.
config = {"configurable": {"session_id": name}}
history = get_session_history(name)

##Only for brand new sessions
if len(history.messages) == 0:
    with st.spinner("Starting Interview"):
        interview_with_memory.invoke(
            {"role": role, "input": "Start the interview"}, config=config
        )

for msg in get_session_history(name).messages:
    with st.chat_message("assistant" if msg.type=="ai" else "user"):
        st.write(msg.content)

if "interview_ended" not in st.session_state:
    st.session_state.interview_ended = False

if not st.session_state.interview_ended:
    answer = st.chat_input("Type your answer...")
    if answer:
        interview_with_memory.invoke({"role": role, "input": answer}, config=config)
        st.rerun()

    if st.button("End Interview & Get Feeedback"):
        st.session_state.interview_ended = True
        st.rerun()
else: 
    st.subheader("Feedback Report")
    with st.spinner("Generating Report"):
        transcript = format_transcript(name)
        report = feedback_chain.invoke({"role": role, "transcript": transcript})
    st.write(report)