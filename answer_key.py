# answer_key.py
import re
from memory_store import get_session_history
from chains import citation_chain
from langchain_community.tools.tavily_search import TavilySearchResults
from resilience import resilient_invoke, resilient_search


search_tool = TavilySearchResults(max_results=3)


def _get_qa_pairs(session_id: str):
    """Pairs each interviewer question with the candidate's immediate next
    answer, regardless of any leading trigger message like 'Start the interview'."""
    messages = get_session_history(session_id).messages
    pairs = []
    for i in range(len(messages) - 1):
        if messages[i].type == "ai" and messages[i + 1].type == "human":
            pairs.append((messages[i].content, messages[i + 1].content))
    return pairs


def _validate_citations(answer_text: str, num_sources: int) -> bool:
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer_text)}
    return all(1 <= n <= num_sources for n in cited) if cited else True


# def show_answers(session_id: str, role: str) -> list[dict]:
#     results = []
#     for question, candidate_answer in _get_qa_pairs(session_id):
#         sources = search_tool.invoke(question)
#         formatted_sources = "\n".join(
#             f"[{j + 1}] {s['content']} ({s['url']})" for j, s in enumerate(sources)
#         )
#         response = citation_chain.invoke({
#             "question": question,
#             "candidate_answer": candidate_answer,
#             "sources": formatted_sources,
#         })
#         results.append({
#             "question": question,
#             "candidate_answer": candidate_answer,
#             "answer_key": response.content,
#             "sources": sources,
#             "citations_valid": _validate_citations(response.content, len(sources)),
#         })
#     return results
# def show_answers(session_id: str, role: str, cache: list[dict] | None = None) -> list[dict]:
#     cache = list(cache) if cache else []
#     pairs = _get_qa_pairs(session_id)
#     already_done = len(cache)

#     for question, candidate_answer in pairs[already_done:]:
#         sources = search_tool.invoke(question)
#         formatted_sources = "\n".join(
#             f"[{j + 1}] {s['content']} ({s['url']})" for j, s in enumerate(sources)
#         )
#         response = citation_chain.invoke({
#             "question": question,
#             "candidate_answer": candidate_answer,
#             "sources": formatted_sources,
#         })
#         cache.append({
#             "question": question,
#             "candidate_answer": candidate_answer,
#             "answer_key": response.content,
#             "sources": sources,
#             "citations_valid": _validate_citations(response.content, len(sources)),
#         })

#     return cache
def show_answers(session_id: str, role: str, cache: list[dict] | None = None) -> list[dict]:
    cache = list(cache) if cache else []
    pairs = _get_qa_pairs(session_id)
    already_done = len(cache)

    for question, candidate_answer in pairs[already_done:]:
        sources = resilient_search(search_tool, question)
        formatted_sources = "\n".join(
            f"[{j + 1}] {s['content']} ({s['url']})" for j, s in enumerate(sources)
        )
        response = resilient_invoke(citation_chain, {
            "question": question,
            "candidate_answer": candidate_answer,
            "sources": formatted_sources,
        })
        cache.append({
            "question": question,
            "candidate_answer": candidate_answer,
            "answer_key": response.content,
            "sources": sources,
            "citations_valid": _validate_citations(response.content, len(sources)),
        })
    return cache