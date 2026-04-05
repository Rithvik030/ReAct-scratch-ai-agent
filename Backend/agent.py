from Backend.tools.calculator import calculate
from Backend.tools.web_search import web_search
import json
import ollama
import re

class Agent:

    def __init__(self):
        self.tools = {"calculator": calculate, "web_search": web_search}
        self.history=[]
        self.max_history=15
        self.failed_queries = set()

    def run(self, input):
        # input validation
        print("Running Agent..")
        retry_count = 0
        max_retries = 2
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
        

        scratchpad = ""

        for step in range(6):
            decision = self.decide_action(input,scratchpad)
            print("Decision made, Proceeding to action...")
            action = decision["action"]
            tool_input = decision["input"]

            
            if action in ["calculator", "final_answer"]:
                is_complete = self.is_query_complete(input, scratchpad)

                if not is_complete:
                    print("Incomplete data — forcing more search")
                    action = "web_search"
                    tool_input = input

            if tool_input in self.failed_queries:
                print("Skipping repeated failed query")
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
            #bad_signals = ["No useful information found.", "Access Denied"]
            print("Checking the usefulness of the tools..")
            if action == "calculator":
                is_useful = True

            elif action == "web_search":
                is_useful = self.is_useful_result(tool_input, result)

            else:
                is_useful = False


            observation = f"""
Step:
- Action: {action}
- Input: {tool_input}
- Result: {result}
- Status: {"useful" if is_useful else "not useful"}
"""
            #checking for failed query if any from observation
            if not is_useful:
                print("The current query didn't give a useful answer.")
                self.failed_queries.add(tool_input)

                if retry_count < max_retries:
                    improved_query = self.generate_better_query(input, scratchpad)

                    print("Retrying with improved query:", improved_query)

                    input = improved_query   # feed back into loop
                    retry_count += 1
                    continue

            #updating the scratchpad memory and printing
            scratchpad +=observation
            print("Scratchpad memory:", scratchpad)
            #updating History
            self.update_history({"query":tool_input,"result":result})

    def decide_action(self, query, scratch_pad):

        print("deciding next step..")
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
11. PERCENTAGE RULE (CRITICAL):
- When calculating percentage of A relative to B:
  → Use: (A / B) * 100

- Carefully identify:
  → A = part
  → B = whole

- Example:
  "What % of Canada is Iceland?"
  → (Iceland / Canada) * 100

- NEVER reverse numerator and denominator
----

 History Usage Rules:

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

    
    def is_useful_result(self, query, result):
        print("Checking whether the result is useful or not...")
        prompt = f"""
User query:
{query}

Result:
{result}

Does this result directly and completely answer the query?

Rules:
- Must answer ALL parts of the query
- Must be specific (no vague words like "soon", "upcoming")
- Must not be generic or partial

Respond ONLY with:
YES or NO
"""

        response = ollama.chat(
        model="gemma3:4b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
        return "YES" in response["message"]["content"].upper()


    def generate_better_query(self, query, scratchpad):
        print("Refining input query...")
        prompt = f"""
The previous search did not return a useful result.

Original query:
{query}

Previous steps:
{scratchpad}

Generate a better, more specific search query.
Only output the improved query.
"""

        response = ollama.chat(
        model="gemma3:4b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3}
    )
        return response["message"]["content"].strip()

    def is_query_complete(self, query, scratchpad):
        print("Checking whether the all the questions in the query been answered..")
        prompt = f"""
User query:
{query}

Current known information:
{scratchpad}

Check if ALL required information to answer the query is present.

Rules:
- Identify all entities and required values in the query
- Check if each one is present in the scratchpad
- If ANY required piece is missing → answer NO
- Only answer YES if everything needed is available

Respond ONLY with:
YES or NO
"""

        response = ollama.chat(
        model="gemma3:4b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
        return response["message"]["content"].strip().upper().startswith("YES")