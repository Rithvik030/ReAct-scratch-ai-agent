# AI Agent System (ReAct-style)

## Overview
This project is a ReAct-style AI agent built from scratch (without using frameworks like LangChain), designed to solve user queries using step-by-step reasoning and tool usage.

The agent dynamically decides actions such as web search or calculation, executes them, and iteratively improves its answer.

---

## Features

- ReAct-style reasoning loop (Thought → Action → Observation)
- Tool usage:
  - Web Search (DuckDuckGo)
  - Calculator
- Scratchpad memory for tracking reasoning steps
- Short-term history for maintaining context
- Reranking of search results for better relevance
- Summarization to extract useful information
- Basic control layer to avoid repeated failed queries
- Validation rules to improve answer reliability

---

## How It Works

1. User enters a query  
2. Agent decides next action using an LLM  
3. Executes tool (web search / calculator)  
4. Stores results in scratchpad memory  
5. Repeats reasoning loop until sufficient information is gathered  
6. Generates final answer  

---

## Example

Ask something (type 'exit' to quit): what is current population of india
IS TIME QUERY: False
Calling LLM
LLM raw response: {"action": "web_search", "input": "current population of india"}
Decision made, Proceeding to action...
Running Tool: web_search
Performing reranked websearch:
Score: 8 | URL: https://en.wikipedia.org/wiki/Demographics_of_India
Score: 10 | URL: https://www.worldometers.info/world-population/india-population/
Score: 10 | URL: https://countrymeters.info/en/India
Score: 8 | URL: https://knowindia.india.gov.in/profile/population.php
Score: 8 | URL: https://www.unfpa.org/data/world-population/IN
Fetching: https://www.worldometers.info/world-population/india-population/ | Score: 10
Fetching: https://countrymeters.info/en/India | Score: 10
Summarising Observation:
Displaying Tool Result: 1,472,766,344 as of Thursday, March 12, 2026, based on Countrymeters’ elaboration of the latest United Nations data.
Scratchpad memory: 
Step:
- Action: web_search
- Input: current population of india
- Result: 1,472,766,344 as of Thursday, March 12, 2026, based on Countrymeters’ elaboration of the latest United Nations data.
- Status: useful

Updating History...
Calling LLM
LLM raw response: {"action": "final_answer", "input": "1,472,766,344"}
Parsed JSON: {'action': 'final_answer', 'input': '1,472,766,344'}
Decision made, Proceeding to action...
Generating Final Answer...
Calling LLM for final answer...

Agent: 1,472,766,344

-> the agent takes the indian population automatically from existing self.history, avoiding an extra llm call for search

Ask something (type 'exit' to quit): what percenage of indian population is population of pakistan
IS TIME QUERY: False
Calling LLM
LLM raw response: {"action": "web_search", "input": "current population of pakistan"}
Decision made, Proceeding to action...
Running Tool: web_search
Performing reranked websearch:
Score: 8 | URL: https://en.wikipedia.org/wiki/Pakistan
Score: 8 | URL: https://en.wikipedia.org/wiki/Demographics_of_Pakistan
Score: 10 | URL: https://www.worldometers.info/world-population/pakistan-population/
Score: 4 | URL: https://data.worldbank.org/indicator/SP.POP.TOTL?locations=PK
Score: 10 | URL: https://countrymeters.info/en/Pakistan
Fetching: https://www.worldometers.info/world-population/pakistan-population/ | Score: 10
Fetching: https://countrymeters.info/en/Pakistan | Score: 10
Summarising Observation:
Displaying Tool Result: 249,131,050 as of Thursday, March 12, 2026, based on Worldometer’s elaboration of the latest United Nations data.
Scratchpad memory: 
Step:
- Action: web_search
- Input: current population of pakistan
- Result: 249,131,050 as of Thursday, March 12, 2026, based on Worldometer’s elaboration of the latest United Nations data.
- Status: useful

Updating History...
Calling LLM
LLM raw response: {"action": "calculator", "input": "249131050 / 1472766344 * 100"}
Decision made, Proceeding to action...
Running Tool: calculator
Displaying Tool Result: 16.915857088597345
Scratchpad memory:
Step:
- Action: web_search
- Input: current population of pakistan
- Result: 249,131,050 as of Thursday, March 12, 2026, based on Worldometer’s elaboration of the latest United Nations data.
- Status: useful

Step:
- Action: calculator
- Input: 249131050 / 1472766344 * 100
- Result: 16.915857088597345
- Status: useful

Updating History...
Calling LLM
LLM raw response: {"action": "final_answer", "input": "16.915857088597345"}
Parsed JSON: {'action': 'final_answer', 'input': '16.915857088597345'}
Decision made, Proceeding to action...
Generating Final Answer...
Calling LLM for final answer...

Agent: 16.92%

## Project Structure
agent_project/

├── agent.py # core agent loop
├── tools.py # tool implementations
├── cli_test.py # CLI interface
├── README.md
└── requirements.txt


---

## Tech Stack

- Python  
- DuckDuckGo Search  
- BeautifulSoup (for scraping)  
- Local LLM via Ollama (Gemma 3 4B)  

---

## Notes

- The system includes control and validation mechanisms to improve reliability, though handling edge cases and consistency is still a work in progress.
- Memory is used cautiously and not blindly reused, especially for time-sensitive queries.
- Built as a learning project to explore LLM-based agent design and real-world limitations.

## Setup 
# Setup Requirements

- Python 3.x  
- Ollama installed and running locally  

Run the following before starting the agent:
existing ollama run gemma3:4b

ollama run model name

make sure you change the model name in the command and also the llm function calls

---
## Running the Project

### CLI Mode (Recommended)
python cli_test.py

---
### Streamlit UI (Requires Backend)

Step 1: Start FastAPI backend
uvicorn main:app --reload

Step 2: Start Streamlit UI
streamlit run app.py

---
Note:
The Streamlit interface depends on the FastAPI backend being active.

## Future Improvements

- Improve validation for edge cases  
- Better memory filtering  
- Add planning layer for structured tasks  
- Improve date/time handling and parsing  
- Expand tool capabilities  
