# agents.py
# ── CHANGE: fixed import — create_agent doesn't exist in LangChain ────────────
from langgraph.prebuilt import create_react_agent
# ── CHANGE: InMemorySaver is the simplest correct checkpointer ───────────────
#    SqliteSaver requires a context manager (with SqliteSaver(...) as mem:)
#    which doesn't work at module level. Use InMemorySaver for now;
#    memory persists for the lifetime of the Python process (i.e. while
#    Streamlit is running), which is exactly what you need.
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# ── CHANGE: added Pydantic model for structured critic output (no more regex) ─
from pydantic import BaseModel
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# ── Model setup ───────────────────────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Single shared checkpointer — lives as long as Streamlit is running.
# Each browser session gets its own thread_id (set in app.py) so memory
# is naturally scoped per user without any DB setup.
memory = InMemorySaver()


# ── Agent 1: Search ───────────────────────────────────────────────────────────
def build_search_agent():
    # ── CHANGE: create_react_agent (was create_agent), added checkpointer + prompt
    return create_react_agent(
        model=llm,
        tools=[web_search],
        checkpointer=memory,                          # ← memory added here
        prompt=(
            "You are a research search agent. "
            "Remember prior searches in this session to avoid redundant queries. "
            "Always return titles, URLs, and detailed snippets."
        ),
    )


# ── Agent 2: Reader ───────────────────────────────────────────────────────────
def build_reader_agent():
    # ── CHANGE: create_react_agent (was create_agent), added checkpointer + prompt
    return create_react_agent(
        model=llm,
        tools=[scrape_url],
        checkpointer=memory,                          # ← memory added here
        prompt=(
            "You are a web scraping agent. "
            "Avoid re-scraping URLs already visited this session. "
            "Extract clean, detailed text content from pages."
        ),
    )


# ── Writer chain ──────────────────────────────────────────────────────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ── CHANGE: structured Pydantic model for critic output ───────────────────────
#    This replaces the fragile regex parse_score() in app.py
class CriticOutput(BaseModel):
    score: int
    strengths: list[str]
    improvements: list[str]
    verdict: str


# ── Critic chain — now returns a typed object instead of raw text ─────────────
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Return a JSON object with these exact keys:
- score: integer from 1 to 10
- strengths: list of 2-3 strength strings
- improvements: list of 2-3 improvement strings
- verdict: one sentence summary

Only return valid JSON. No extra text."""),
])

# ── CHANGE: .with_structured_output() replaces StrOutputParser() ──────────────
#    critic_chain.invoke(...) now returns a CriticOutput object, not a string
critic_chain = critic_prompt | llm.with_structured_output(CriticOutput)