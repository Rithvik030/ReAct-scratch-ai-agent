# MyAgent
## Overview
This project is a custom-built ReAct-style AI agent developed from scratch
It solves user queries using step-by-step reasoning, tool usage, and iterative self-correction.

Instead of generating answers directly, the agent dynamically decides what actions to take (e.g., web search or calculation), evaluates results, and refines its approach before producing a final answer.

---

## Features

- ReAct-style reasoning loop (Reason → Act → Observe)
- Web search with custom retrieval pipeline
- Calculator tool for numerical reasoning
- Adaptive query refinement (self-correction after failures)
- Semantic usefulness evaluation to filter poor results
- Completion check to ensure all required information is gathered
- Scratchpad memory for step-by-step reasoning tracking
- Basic Streamlit UI for interaction

---

## What is ReAct?

ReAct stands for:

> **Reason + Act**

The agent follows an iterative loop:

1. **Reason** → Decide what to do next  
2. **Act** → Use a tool (web search / calculator)  
3. **Observe** → Analyze the result  
4. **Repeat** → Continue until enough information is gathered  

This enables:
- multi-step reasoning  
- dynamic decision-making  
- error recovery  

---

## How It Works


User Query
↓
Decide Action (LLM)
↓
Tool Execution (Web Search / Calculator)
↓
Summarize Result
↓
Usefulness Check
↓
Completion Check
↓
Retry (if needed)
↓
Final Answer


---

## Example

Ask: what is current population of india

Agent:
- Action: web_search  
- Input: current population of india  
- Result: 1,472,766,344  

Final Answer: 1,472,766,344

---

Ask: what percentage of indian population is population of pakistan

Agent:
- Action: web_search → population of Pakistan  
- Result: 249,131,050  

- Action: calculator  
- Input: 249131050 / 1472766344 * 100  
- Result: 16.91  

Final Answer: 16.92%

## Retrieval Pipeline

- Uses `requests` to fetch web data  
- Uses `BeautifulSoup` to parse and extract content  
- Applies manual reranking based on query relevance  
- Summarizes results for cleaner reasoning  

---

## Self-Correction Mechanism

If results are not useful:
- The agent refines the query  
- Retries with improved input  
- Continues until meaningful information is found  

---

## Project Structure


agent_project/

├── Backend/
│ ├── agent.py
│ ├── tools/
│ └── ...
├── Frontend/
│ └── app.py
├── cli_test.py
├── README.md
└── requirements.txt


---

## Tech Stack

- Python  
- Local LLM via Ollama (Gemma 3 4B)  
- requests, BeautifulSoup  
- DuckDuckGo Search  
- Streamlit  

---

## Setup

### Requirements
- Python 3.x  
- Ollama installed and running  

Run:

ollama run gemma3:4b


---

##  Running the Project

### CLI Mode (recommended)

python cli_test.py


### Streamlit UI

Start backend:

uvicorn main:app --reload


Start UI:

streamlit run app.py


---

## Notes

- The project focuses on reasoning and system design rather than direct answer generation  
- Includes validation mechanisms to improve reliability  
- Designed as a learning project to explore real-world of LLM-based agents  

---

## Future Improvements

- Improve validation for edge cases  
- Better memory filtering  
- Add planning layer for structured tasks  
- Improve time/date handling  
- Expand tool capabilities  