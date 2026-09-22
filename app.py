import streamlit as st

from dotenv import load_dotenv
load_dotenv()
from langchain_core.runnables.history import RunnableWithMessageHistory
from chains import interview_chain, feedback_chain
from memory_store import get_session_history
from answer_key import show_answers
from resilience import resilient_invoke

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

import uuid   # add to your existing imports at the top

# ... st.set_page_config(...), st.title(...) ...

# One unguessable token per browser session
if "session_token" not in st.session_state:
    params = st.query_params
    if "sid" in params:
        st.session_state.session_token = params["sid"]
    else:
        st.session_state.session_token = str(uuid.uuid4())
        st.query_params["sid"] = st.session_state.session_token

session_id = st.session_state.session_token

with st.sidebar:
    name = st.text_input("Your name (for display only)")
    role = st.text_input("Role you're interviewing for", placeholder="e.g. AI Engineer")
    start_clicked = st.button("Start / Resume Interview")
    st.caption("Bookmark this page's URL to resume your session later.")

# with st.sidebar:
#     name = st.text_input("Your name (this is your session ID)")
#     role = st.text_input("Role you're interviewing for", placeholder="e.g. AI Engineer")
#     start_clicked = st.button("Start / Resume Interview")

if "started" not in st.session_state:
    st.session_state.started = False
if start_clicked and name and role:
    st.session_state.started = True

if not st.session_state.started:
    st.info("Enter your name and role, then click 'Start / Resume Interview")
    st.stop()

#tell langchain which student's session to read/write and checks it.
config = {"configurable": {"session_id": session_id}}
history = get_session_history(session_id)

##Only for brand new sessions
# if len(history.messages) == 0:
#     with st.spinner("Starting Interview"):
#         interview_with_memory.invoke(
#             {"role": role, "input": "Start the interview"}, config=config
#         )
if len(history.messages) == 0:
    with st.spinner("Starting Interview"):
        resilient_invoke(interview_with_memory, {"role": role, "input": "Start the interview"}, config=config)

# for msg in get_session_history(name).messages:
#     with st.chat_message("assistant" if msg.type=="ai" else "user"):
#         st.write(msg.content)
question_num = 0
for msg in get_session_history(session_id).messages:
    if msg.type == "ai":
        question_num += 1
        with st.chat_message("assistant"):
            st.markdown(f"**Question {question_num}:**")
            st.write(msg.content)
    else:
        with st.chat_message("user"):
            st.write(msg.content)

if "interview_ended" not in st.session_state:
    st.session_state.interview_ended = False

if not st.session_state.interview_ended:
    answer = st.chat_input("Type your answer...")
    if answer:
        # interview_with_memory.invoke({"role": role, "input": answer}, config=config)
        # st.rerun()
        resilient_invoke(interview_with_memory, {"role": role, "input": answer}, config=config)
        st.rerun()

    if st.button("End Interview & Get Feeedback"):
        st.session_state.interview_ended = True
        st.rerun()
else: 
    st.subheader("Feedback Report")
    # with st.spinner("Generating Report"):
    #     transcript = format_transcript(session_id)
    #     report = feedback_chain.invoke({"role": role, "transcript": transcript})
    # st.write(report)
    if "feedback_cache" not in st.session_state:
        st.session_state.feedback_cache = {}

    history_messages = get_session_history(session_id).messages
    cached = st.session_state.feedback_cache.get(session_id)

    if cached and cached["message_count"] == len(history_messages):
        report = cached["report"]
    else:
        with st.spinner("Generating Report"):
            transcript = format_transcript(session_id)
            report = resilient_invoke(feedback_chain, {"role": role, "transcript": transcript})
        st.session_state.feedback_cache[session_id] = {"report": report, "message_count": len(history_messages)}
    st.write(report)
    
    st.subheader("Answer Key")

    if "answer_key_cache" not in st.session_state:
        st.session_state.answer_key_cache = {}

    # if st.button("Show me answers"):
    #     with st.spinner("Looking up sources and generating answer key..."):
    #         cached = st.session_state.answer_key_cache.get(name, [])
    #         answer_key = show_answers(name, role, cache=cached)
    #     st.session_state.answer_key_cache[name] = answer_key        
    #     for idx, item in enumerate(answer_key, start=1):
    #         st.markdown(f"### Question {idx}")
    #         st.markdown(f"**Interviewer asked:** {item['question']}")
    #         st.markdown(f"**Your answer:** {item['candidate_answer']}")
    #         st.markdown("**Ideal answer & feedback:**")
    #         st.write(item["answer_key"])
    #         if not item["citations_valid"]:
    #             st.caption("Some citations may not be fully grounded in the sources shown.")
    #         with st.expander("Sources"):
    #             for s_idx, s in enumerate(item["sources"], start=1):
    #                 st.write(f"[{s_idx}] {s['url']}")
    #         st.divider()
        
    if st.button("Show me answers"):
        with st.spinner("Looking up sources and generating answer key..."):
            cached = st.session_state.answer_key_cache.get(session_id, [])
            st.session_state.answer_key_cache[session_id] = show_answers(session_id, role, cache=cached)

    # Renders whatever is cached, on every rerun — not just the click that generated it
    if session_id in st.session_state.answer_key_cache:
        for idx, item in enumerate(st.session_state.answer_key_cache[session_id], start=1):
            st.markdown(f"### Question {idx}")
            st.markdown(f"**Interviewer asked:** {item['question']}")
            st.markdown(f"**Your answer:** {item['candidate_answer']}")
            st.markdown("**Ideal answer & feedback:**")
            st.write(item["answer_key"])
            if not item["citations_valid"]:
                st.caption("Some citations may not be fully grounded in the sources shown.")
            with st.expander("Sources"):
                for s_idx, s in enumerate(item["sources"], start=1):
                    st.write(f"[{s_idx}] {s['url']}")
            st.divider()

    if st.button("Continue Interview"):
        st.session_state.interview_ended = False
        st.rerun()  