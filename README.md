# MyAgent
## Overview
This project is an AI agent that answers user queries by combining reasoning, web search, and tool usage instead of relying on direct LLM responses.

It is a custom-built ReAct-style AI agent developed from scratch that solves queries using step-by-step reasoning, tool usage, and iterative self-correction.

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

```bash
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

```

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

## 📁 Project Structure

```bash
agent_project/
│
├── Backend/
│   ├── agent.py
│   └── tools/
│       ├── web_search.py
│       └── calculator.py
│
├── Frontend/
│   └── app.py
│
├── cli_test.py
├── README.md
└── requirements.txt
```


---

## Tech Stack

- Python  
- Local LLM via Ollama 
- requests, BeautifulSoup  
- DuckDuckGo Search  
- Streamlit  

---

## Setup

### Requirements
- Python 3.x  
- Ollama installed and running  

---

### Model Setup

By default, the agent uses:

  gemma3:4b

If you are using this model locally, make sure to pull it first:

  ollama pull gemma3:4b

---

### Using a Different Model (

You can override the default model using an environment variable.

Windows (CMD):

  set MODEL_NAME=your_model_name

---

### Important

- If you set a different **local model**, you must pull it before running:

    ollama pull your_model_name

- If you use a **cloud model** (e.g., gemma4:31b-cloud), no pull is required

- If `MODEL_NAME` is not set, the default `gemma3:4b` will be used

To explore available local and cloud models, refer to the Ollama website: https://ollama.com/library

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