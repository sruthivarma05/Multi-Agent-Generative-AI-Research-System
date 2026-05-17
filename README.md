# Multi-Agent-Generative-AI-Research-System
Multi-Agent Generative AI Research System built with LangChain, LangGraph, OpenAI GPT-4o-mini, Tavily, Playwright, and Streamlit. AI agents collaborate to search the web, scrape content, generate research reports, and critique outputs autonomously.

# 🔬 ResearchMind — Multi-Agent Generative AI Research System

ResearchMind is an advanced **Generative AI-powered Multi-Agent Research Assistant** that autonomously performs web research, content extraction, report generation, and AI-based report evaluation.

Built using:
- LangChain
- LangGraph
- OpenAI GPT-4o-mini
- Tavily Search API
- Playwright
- Streamlit

The system demonstrates how multiple AI agents can collaborate together in a pipeline to solve complex research tasks automatically.

---

#  Features

##  Multi-Agent AI Architecture
The project uses specialized AI agents working together:

### 1. Search Agent
- Searches the web using Tavily API
- Retrieves recent and reliable information
- Uses caching to reduce repeated API calls

### 2. Reader Agent
- Scrapes websites using:
  - BeautifulSoup
  - Requests
  - Playwright (for JavaScript-rendered sites)
- Automatically detects dynamic websites
- Includes retry logic for robustness

### 3. Writer Agent
- Uses GPT-4o-mini to generate:
  - Structured research reports
  - Key findings
  - Conclusions
  - Source references

### 4. Critic Agent
- Reviews generated reports
- Gives:
  - AI-generated quality score
  - Strengths
  - Improvements
  - Final verdict

---

#  Generative AI Concepts Used

This project showcases several modern GenAI engineering concepts:

- Large Language Models (LLMs)
- Multi-Agent Systems
- AI Tool Calling
- Autonomous AI Workflows
- Retrieval-Augmented Generation (RAG)
- Structured Output Generation
- AI Memory Management
- Agent Orchestration using LangGraph
- Prompt Engineering
- AI Critique & Self-Evaluation

---

#  System Architecture

```text
User Topic
    ↓
Search Agent
    ↓
Reader Agent
    ↓
Writer Agent
    ↓
Critic Agent
    ↓
Final Research Report

project structure:
├── app.py              # Streamlit frontend UI
├── agents.py           # AI agents and chains
├── tools.py            # Search & scraping tools
├── pipeline.py         # Main multi-agent workflow
├── requirements.txt
└── README.md
