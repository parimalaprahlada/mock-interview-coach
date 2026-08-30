import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from prompts import interview_prompt, feedback_prompt
from langchain_core.output_parsers import StrOutputParser
api_key = os.environ["api_key"]
base_url = os.environ["base_url"]

groq_llm = ChatOpenAI(
    model="groq/openai/gpt-oss-20b", base_url=base_url,api_key=api_key
)

openai_llm = ChatOpenAI(
    model="groq/openai/gpt-oss-20b", base_url=base_url,api_key=api_key
)


##Langchain Chaining, Prompt->output->parser
#Extract plain text from AImessage
interview_chain = interview_prompt|groq_llm|StrOutputParser()
feedback_chain = feedback_prompt|openai_llm|StrOutputParser()