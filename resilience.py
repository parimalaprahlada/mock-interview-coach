import time
import threading
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError

_lock = threading.Lock()
_last_call_time = [0.0]
MIN_INTERVAL = 2.0  # seconds between outgoing calls — tune to your actual Groq RPM limit

def _throttle():
    with _lock:
        elapsed = time.time() - _last_call_time[0]
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        _last_call_time[0] = time.time()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIError, APIConnectionError, APITimeoutError)),
    reraise=True,
)
def resilient_invoke(chain, payload, **kwargs):
    """Throttle + retry wrapper for any LangChain chain's .invoke()."""
    _throttle()
    return chain.invoke(payload, **kwargs)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def resilient_search(search_tool, query):
    """Throttle + retry wrapper for Tavily (or any) search tool."""
    _throttle()
    return search_tool.invoke(query)