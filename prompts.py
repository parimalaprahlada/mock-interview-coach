from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

#building Interviewer's prompt template
interview_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a strict but fair technical interviewer for the role of {role}. "
     "Ask exactly ONE interview question at a time. "
     "Never repeat a question that has already been asked in this conversation. "
     "Keep questions short and clear."),
    MessagesPlaceholder("history"),
    ("human", "{input}")
]
    
)

#Building Evaluator's prompt template
feedback_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a senior hiring manager. Below is a full mock interview transcript "
         "for the role of {role}. Write a short feedback report: 2-3 strengths, "
         "2-3 areas to improve, and an overall readiness score out of 10."),
    ("human", "{transcript}")
]
    
)

citation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "The interview is over. For the question and the candidate's answer below, "
     "use ONLY the provided sources to: "
     "1) State the ideal answer clearly. "
     "2) Compare it to the candidate's answer. "
     "3) Note gaps or inaccuracies, specifically and constructively. "
     "Cite sources inline as [1], [2], matching the numbered list. "
     "Never cite anything not in the source list — if the sources don't fully "
     "cover something, say so explicitly rather than filling the gap from your "
     "own knowledge."),
    ("human",
     "Question: {question}\n\n"
     "Candidate's answer: {candidate_answer}\n\n"
     "Sources:\n{sources}")
])