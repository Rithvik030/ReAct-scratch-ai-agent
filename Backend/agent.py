from Backend.tools.calculator import calculate
from Backend.tools.web_search import web_search
import json
import ollama
import re
from datetime import datetime
import pytz


class Agent:

    def __init__(self):
        self.tools = {"calculator": calculate, "web_search": web_search}
        self.history=[]
        self.max_history=15
        self.failed_queries = set()

    def run(self, input):
        # input validation
        clean = input.strip()

        if not clean:
            return "Please provide a valid question."

        if clean.lower() in ["hi", "hey", "hello"] or clean.lower().startswith(("+","-","*","/","%",".",",")):
            return "Hey! How can I help you?"

        # math expression detection
        if re.fullmatch(r"[0-9+\-*/(). ]+", clean):
            pass  # allow it to go to agent

        elif len(clean.split()) <= 1:
            return "Can you tell me a bit more about what you're looking for?"
        
        print("IS TIME QUERY:", self.is_time_query(input))
        if self.is_time_query(input):
            print("TIME FUNCTION CALLED")
            result = self.get_time_for_location(input)
            if result:
                return result


        scratchpad = ""

        for step in range(6):
            decision = self.decide_action(input,scratchpad)
            print("Decision made, Proceeding to action...")
            action = decision["action"]
            tool_input = decision["input"]

            if tool_input in self.failed_queries:
                print("⚠️ Skipping repeated failed query")
                continue

            if action == "final_answer":
                print("Generating Final Answer...")
                return self.generate_final_answer(input,scratchpad)


            if action in self.tools:
                tool_function = self.tools[action]
                print("Running Tool:", action)
                result = tool_function(tool_input)

                if action=="web_search":
                    print("Summarising Observation:")
                    result=self.summarize_observation(tool_input, result)
                    if "next" in input.lower():
                        if not self.is_future_date(result):
                            result = "No useful information found."
                
                print("Displaying Tool Result:",result)

            #storing the observation of the current step
            bad_signals = ["No useful information found.", "Access Denied"]


            observation = f"""
Step:
- Action: {action}
- Input: {tool_input}
- Result: {result}
- Status: {"not useful" if any(bad in result for bad in bad_signals) else "useful"}
"""
            #checking for failed query if any from observation
            if "not useful" in observation:
                self.failed_queries.add(tool_input)
            #updating the scratchpad memory and printing
            scratchpad +=observation
            print("Scratchpad memory:", scratchpad)
            #updating History
            self.update_history({"query":tool_input,"result":result})

    def decide_action(self, query, scratch_pad):

        print("Calling LLM")
        prompt = f"""
You are an AI agent that decides actions.

Available tools:
- calculator
- web_search

Your task is to decide the NEXT action.

Respond ONLY in JSON:
{{"action": "<tool_name or final_answer>", "input": "<input>"}}

---

Guidelines:

1. Understand the query deeply:
   - Identify exactly what is being asked
   - Identify ALL required pieces of information

2. Tool usage:
   - calculator → for math or comparisons
   - web_search → for real-world or unknown data

3. STRICT NO GUESSING:
   - If any required information is missing → you MUST search
   - NEVER assume or invent answers

4. COMPLETION AWARENESS (VERY IMPORTANT):
   You can ONLY return "final_answer" if:
   - The answer is explicitly present in previous steps
   - AND all parts of the query are fully satisfied

   Otherwise:
   → continue searching

5. USEFULNESS CHECK:
   A result is useful ONLY if it directly answers the query.

   Reject:
   - links
   - navigation pages
   - general descriptions
   - incomplete data

6. QUERY REFINEMENT:
   If a result is not useful:
   - Identify what is missing
   - Reformulate a better, more specific query

   Example:
   "next IPL match"
   → "next IPL match teams date time"

7. COMPARISON & NUMERIC REASONING:
   When comparing values:
   - Convert to comparable form
   - Use same units
   - If one value is a range:
       → evaluate using min and max OR clear representative value
   - Use calculator if needed
   - DO NOT make assumptions

8. MEMORY USAGE:
   - Use previous steps ONLY if they directly answer the query
   - Ignore irrelevant or incomplete memory

9. OUTPUT DISCIPLINE:
   - Ensure correct units (%, km, etc.)
   - Do not output raw or partial numbers
   - Keep answers precise

10. EFFICIENCY:
   - Avoid repeating failed queries
   - Try improved queries instead

----

🔥 History Usage Rules:

- Carefully check "Previous steps" before deciding
- If the answer can be directly obtained from previous steps → use "final_answer"
- Prefer using previous information instead of calling web_search again
- If previous steps contain enough context to infer the answer → do NOT search
- Only use web_search if required information is missing

---
Available Information:

User query:
{query}

Previous steps:
{scratch_pad}

memory:
{json.dumps(self.history, indent=2)}
"""
        response = ollama.chat(
            model="gemma3:4b", messages=[{"role": "user", "content": prompt}]
        )

        output = response["message"]["content"]
        print("LLM raw response:", output)

        # removing the markdown code blocks
        output = output.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(output)
            if parsed["action"] == "final_answer":
                print("Parsed JSON:", parsed)
            return parsed

        except Exception as e:
            print("JSON Parsing error:", e)
            return {"action": "final_answer", "input": "Sorry, I encountered an error."}

    # function for summarising the results from perfroming websearch
    def summarize_observation(self, query, results):
        text = str(results)
        prompt = f"""
You are extracting the MOST RELEVANT and FACTUALLY CORRECT answer from web search results.

User query:
{query}

Search results:
{text}

RULES:

1. Return a DIRECT, SPECIFIC, and FACTUALLY CORRECT answer to the user query.

2. The result MUST directly and COMPLETELY answer the query — not just be related.

3. DO NOT return:
   - vague summaries (e.g., "tomorrow", "soon", "upcoming")
   - general descriptions
   - headings or titles
   - navigation text
   - error messages (e.g., "Access Denied")
   - statements like "available on website" or "full schedule"
   - partial information (missing key details)

4. FACT QUALITY REQUIREMENT (VERY IMPORTANT):
   Only return information that is:
   - specific
   - explicit
   - clearly stated in the text

   If any part is unclear, ambiguous, or inferred → REJECT it.

5. COMPLETENESS REQUIREMENT (CRITICAL):

   For "next match" type queries:
   - MUST include:
     → teams (or opponent)
     → date (or time)

   For numeric or factual queries:
   - MUST include the exact value

   If ANY required detail is missing → DO NOT return it.

6. Prefer specific factual information such as:
   - exact dates (not relative like "tomorrow")
   - full names (teams, entities)
   - exact numbers

7. If multiple answers exist:
   - choose the most precise and complete one

8. If the result does NOT directly and completely answer the query:
   return EXACTLY:
   "No useful information found."

9. NEVER guess, infer, or complete missing information.

10. Output:
   - maximum 1–2 sentences
   - no links
   - no explanations
"""

        response = ollama.chat(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 120, "temperature": 0.2},
        )
        return response["message"]["content"]

    def generate_final_answer(self, query, scratchpad):

        print("Calling LLM for final answer...")

        prompt = f"""
You are an AI assistant.

Available Information:

User query:
{query}

Previous steps:
{scratchpad}

memory:
{json.dumps(self.history, indent=2)}

Instructions:

- Your job is to find a CLEAR and DIRECT answer from the provided information

- ONLY answer if the information explicitly contains the answer
- DO NOT guess
- DO NOT infer
- DO NOT combine multiple vague sources

- If no result clearly answers the query, return EXACTLY:
"I could not find sufficient information."

- If an answer is found:
  - Use only one best source
  - Keep it concise (1 sentence)
  - Do not add extra details



MULTI-PART ANSWER RULE:

- If the query asks for multiple pieces of information:
  → ALL parts must be answered

- Do NOT return partial answers

- If some parts are missing:
  → return "I could not find sufficient information."

QUESTION TYPE DETECTION:

- Identify the type of query:

  → factual:
     requires direct information (date, time, value, name)
     → MUST be explicitly present in data

  → comparative:
     requires comparing values
     → use numeric reasoning if needed

  → logical:
     requires reasoning based on known facts
     → inference is allowed ONLY from available data

- Choose answering method accordingly

- NEVER mix types incorrectly


REASONING RULE:

- If the query requires logical reasoning (not direct factual lookup):
  → You MAY combine available facts from previous steps or memory

- Only allow reasoning if:
  → all required base facts are present
  → reasoning is straightforward and certain

- Example:
  temperature = 36°C
  → building a snowman is not possible

- In such cases:
  → DO NOT reject the answer
  → Provide a clear, concise conclusion

- NEVER invent new facts
- ONLY reason using available information

RETURN ONLY THE FINAL ANSWER
"""
        response = ollama.chat(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
        )

        return response["message"]["content"]
    
    def update_history(self,entry):
        print("Updating History...")

        self.history.append(entry)
        #if the no of items in history exceed max history, it pops the oldest one, for every new entry into history
        if len(self.history)>self.max_history:
            self.history.pop(0)


    def is_time_query(self, query):
        query = query.lower()

        time_words = ["time", "date"]
        location_words = ["in", "at"]  # key signal

        return (
        any(word in query for word in time_words)
        and any(loc in query for loc in location_words)
    )

    def get_time_for_location(self, query):
        query = query.lower()

        tz = None  # 🔥 always initialize

        # basic mapping
        if "hyderabad" in query or "india" in query:
            tz = pytz.timezone("Asia/Kolkata")

        elif "london" in query or "uk" in query:
            tz = pytz.timezone("Europe/London")

        elif "new york" in query or "usa" in query:
            tz = pytz.timezone("America/New_York")

        # 🔥 fallback if unknown location
        if tz is None:
            print("tz is none, heading back to the agent")
            return None

        now = datetime.now(tz)

        if "time" in query and "date" in query:
            return now.strftime("%I:%M %p, %A, %B %d, %Y")

        elif "time" in query:
            return now.strftime("%I:%M %p")

        elif "date" in query:
            return now.strftime("%A, %B %d, %Y")
        return None


    def is_future_date(self, text):
        # patterns to extract date
        print("Checking date...")
        patterns = [
            r"\d{1,2} \w+ \d{4}",      # 13 April 2026
            r"\w+ \d{1,2}, \d{4}",     # December 26, 2025
            r"\d{1,2} \w{3} \d{4}",    # 01 Apr 2026
            r"\w{3} \d{1,2}, \d{4}"    # Apr 01, 2026
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group()

                formats = [
                    "%d %B %Y",
                    "%B %d, %Y",
                    "%d %b %Y",
                    "%b %d, %Y"
                ]

                for fmt in formats:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return date_obj > datetime.now()
                    except:
                        continue

        return True  # fallback
