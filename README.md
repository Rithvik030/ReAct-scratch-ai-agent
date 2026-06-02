# MyAgent

## Overview

MyAgent is a custom-built AI workflow agent that answers user queries through iterative reasoning, tool orchestration, requirement tracking, and validation instead of relying solely on direct LLM responses.

The system decomposes user queries into information requirements, dynamically decides which actions to take, gathers information through tools, validates results, and continues reasoning until sufficient information is collected to answer the request.

The project was built from scratch to explore agent architectures, retrieval workflows, multi-step reasoning, and autonomous decision-making systems.

---

## Core Idea

Instead of attempting to answer an entire query at once, the agent first extracts the underlying information requirements and solves them individually before generating a final answer.

### Example

User Query:

> What is the next Tottenham match and the population of Norway?

Extracted Requirements:

- Tottenham → next match
- Norway → population

The agent then focuses on solving each requirement before synthesizing a final response.

---

## Features

### Requirement Extraction

The agent identifies the actual information requirements hidden within a query before attempting to solve it.

Example:

User Query:

> What is the difference between the population of Norway and Sweden?

Extracted Requirements:

- Norway → population
- Sweden → population

---

### Requirement-Aware Execution

The agent tracks which requirements have already been satisfied and focuses only on unresolved requirements.

Benefits:

- Reduces redundant searches
- Improves efficiency
- Enables multi-step workflows

---

### ReAct-Inspired Reasoning Loop

The execution engine follows a ReAct-style workflow:

1. Reason
2. Act
3. Observe
4. Repeat

Rather than answering immediately, the agent iteratively gathers information until enough evidence exists to answer the query.

---

### Tool Orchestration

The agent dynamically selects tools based on the task.

Available tools:

- Web Search
- Calculator

---

### Self-Correction

If retrieval results are poor or irrelevant, the agent attempts to generate improved search queries and retry before giving up.

---

### Retrieval Validation

The system evaluates retrieved information before accepting it.

It attempts to reject:

- Navigation pages
- Irrelevant content
- Incomplete information
- Low-quality results

---

### State Tracking

The agent maintains internal state including:

- Requirements
- Collected facts
- Conversation history
- Failed queries

This enables multi-step reasoning and workflow execution.

---

## System Architecture

```text
User Query
    │
    ▼
Requirement Extraction
    │
    ▼
Requirement Tracking
    │
    ▼
Decide Next Action
    │
 ┌──┴───────────┐
 │              │
 ▼              ▼
Web Search   Calculator
 │              │
 └──────┬───────┘
        │
        ▼
Result Validation
        │
        ▼
State Update
        │
        ▼
Query Complete?
     │      │
     │ No   │ Yes
     ▼      ▼
 Continue  Final Answer
```

---

## Example Workflow

Query:

> What is the difference between the population of Norway and Sweden?

Execution:

1. Extract requirements
   - Norway population
   - Sweden population

2. Retrieve Norway population

3. Retrieve Sweden population

4. Perform calculation

5. Generate final answer

---

## Retrieval Pipeline

The web retrieval system includes:

- DuckDuckGo Search
- Domain-aware retrieval
- Query categorization
- Content extraction
- Result ranking
- Summarization
- Validation

---

## Project Structure

```text
Agent_plat/
│
├── Backend/
│   ├── agent.py
│   ├── main.py
│   │
│   └── tools/
│       ├── calculator.py
│       └── web_search.py
│
├── Frontend/
│   └── app.py
│
├── cli_test.py
├── requirements.txt
└── README.md
```

---

## Tech Stack

- Python
- Ollama
- FastAPI
- Streamlit
- DuckDuckGo Search
- Requests
- BeautifulSoup

---

## Model Setup

By default, the agent uses:

```text
gemma3:4b
```

Pull the model before running:

```bash
ollama pull gemma3:4b
```

### Using a Different Model

You can override the default model using an environment variable.

Windows (CMD):

```cmd
set MODEL_NAME=your_model_name
```

Windows (PowerShell):

```powershell
$env:MODEL_NAME="your_model_name"
```

### Important

If you use a different local model, pull it before running:

```bash
ollama pull your_model_name
```

If `MODEL_NAME` is not set, the default model will be used:

```text
gemma3:4b
```

Available Ollama models:

https://ollama.com/library

---

## Running the Project

### Start Backend

```bash
uvicorn Backend.main:app --reload
```

### Start Frontend

```bash
streamlit run Frontend/app.py
```

### CLI Mode

```bash
python cli_test.py
```

---

## Current Capabilities

- Multi-step reasoning
- Requirement extraction
- Requirement-aware execution
- Tool orchestration
- Self-correction
- Query refinement
- Retrieval validation
- State tracking
- Numerical reasoning

---

## Future Improvements

- Refactor and modularize the agent architecture
- Improve requirement dependency handling
- Improve stopping logic and answer sufficiency checks
- Improve query categorization and routing
- Reduce unnecessary tool calls and over-reasoning
- Expand tool capabilities
- Improve retrieval quality and validation
- Explore Agentic RAG integration

---

## Purpose

This project was built to explore how autonomous AI workflows can be designed from first principles, focusing on reasoning loops, retrieval orchestration, validation, and requirement-driven execution rather than simple prompt-response interactions.