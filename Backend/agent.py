from Backend.tools.calculator import calculate
from Backend.tools.web_search import web_search
import json
import ollama
import re
import os
MODEL=os.getenv("MODEL_NAME",'gemma4:31b-cloud')
print(f"Using model:{MODEL}")


class Agent:

    def __init__(self):
        self.tools = {"calculator": calculate, "web_search": web_search}
        self.history = []
        self.max_history = 15
        self.failed_queries = set()
        self.state = {
            "requirements": [],
            "facts": []
        }
        self.requirements = {}

    def run(self, input):
        self.fresh_fetched = False
        clean = input.strip()

        if not clean:
            return "Please provide a valid question."

        if clean.lower() in ["hi", "hey", "hello"]:
            return "Hey! How can I help you?"

        if re.fullmatch(r"[0-9+\-*/(). ]+", clean):
            pass

        elif len(clean.split()) <= 1:
            return f"{clean}? Can you tell me more?"

        print("Resetting agent state..")
        self.state = {
            "requirements": [],
            "facts": []
        }

        print("Running Agent..")

        self.plan = self.build_plan(input)
        self.plan_idx = 0

        self.state["requirements"] = self.extract_requirements(input)

        print("Requirements:", self.state["requirements"])

        scratchpad = ""
        retry_count = 0
        max_retries = 2

        for step in range(10):

            print("\n--- LOOP STEP ---")
            print("Scratchpad:", scratchpad)

            # MAIN REASONER
            decision = self.decide_action(input, scratchpad)

            action = decision["action"]
            tool_input = decision["input"]

            if action == "web_search" and self.plan_idx < len(self.plan):
                self.plan_idx += 1

            print(f"Action: {action} | Input: {tool_input}")

            # Stop if reasoner decides
            if action == "final_answer":
                return self.generate_final_answer(input, scratchpad)

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
                
                print("Displaying Tool Result:",result)


            #storing the observation of the current step
            #bad_signals = ["No useful information found.", "Access Denied"]
            print("Checking the usefulness of the tools..")

            # TOOL EXECUTION
            if action == "calculator":
                print("Executing calculator with input from reasoner...")
                try:
                    result = calculate(tool_input)
                except Exception:
                    result = "Invalid calculation."

            elif action == "web_search":
                print("Running tool: web_search")
                result = web_search(tool_input)
                

                print("Summarising Observation:")
                self.fresh_fetched = True
                result = self.summarize_observation(tool_input, result)

            else:
                result = "Unsupported action."

            print("Result:", result)

            # requirement status update
            for req in self.state["requirements"]:

                if req["answered"]:
                    continue

                satisfied = self.is_requirement_answered(req, result)

                if satisfied:

                    req["answered"] = True
                    req["answer"] = result

                    print(f"Requirement satisfied: {req['id']}")

            # store facts
            self.state["facts"].append(result)
            print("State:", self.state)

            # usefulness check
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

            if not is_useful:
                self.failed_queries.add(tool_input)

                if retry_count < max_retries:
                    improved_query = self.generate_better_query(input, scratchpad)
                    input = improved_query
                    retry_count += 1
                    continue

            scratchpad += observation
            self.update_history({"query": tool_input, "result": result})

            #  EARLY STOPPING
            '''if self.is_query_complete(input, scratchpad):
                print("Early stop → answer found")
                return self.generate_final_answer(input, scratchpad)'''

        return "Could not find sufficient information."


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

12. REQUIREMENT-FOCUSED EXECUTION (CRITICAL):

- Carefully examine the requirements state
- Identify which requirements are already answered
- Focus ONLY on unresolved requirements
- Choose ONE unresolved requirement at a time
- Your next action must directly help solve that requirement
- Do NOT jump randomly between unrelated tasks
- Do NOT attempt to solve the entire query at once

Examples:

If:
- norway_population = answered
- tottenham_next_match = unanswered

Then:
→ your next action MUST focus on Tottenham only

Do NOT search Norway again.
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

Requirements state:
{json.dumps(self.state["requirements"], indent=2)}
"""
        response = ollama.chat(
            model=MODEL, messages=[{"role": "user", "content": prompt}]

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
            model=MODEL,
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
            model=MODEL,
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

        # basic sanity check
        if not result or result.strip() == "":
            return False

        # reject obvious garbage
        bad_signals = [
    "no useful information",
    "access denied",
    "error",
]

        if any(bad in result.lower() for bad in bad_signals):
            return False
        
        if any(char.isdigit() for char in result):
            return True

        prompt = f"""
User query:
{query}

Result:
{result}

Does this result help answer the query?

Rules:
- If the result contains relevant facts → YES
- If it partially answers the query → YES
- If it includes useful data (numbers, names, entities) → YES
- Only say NO if it is completely irrelevant or empty

Respond ONLY with:
YES or NO
"""

        response = ollama.chat(
        model=MODEL,
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
        model=MODEL,
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

Can the agent already answer the query using the available information?

Rules:
- If the answer can be directly computed or inferred → YES
- If required values (numbers/facts) are present → YES
- If calculation has already been performed → YES
- Even if answer is in natural language → YES
- Only say NO if critical data is missing



Respond ONLY with:
YES or NO
"""

        response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
        return response["message"]["content"].strip().upper().startswith("YES")
    
    def extract_requirements(self, query):

        print("Extracting requirements..")

        prompt = f"""
Extract the ACTUAL information requirements from the user query.

Query:
{query}

Return STRICT JSON ONLY.

Format:

[
  {{
    "id": "requirement_id",
    "entity": "entity_name",
    "metric": "metric_name"
  }}
]

Examples:

Query:
"What is the population of Norway?"

Output:
[
  {{
    "id": "norway_population",
    "entity": "norway",
    "metric": "population"
  }}
]

Query:
"What is the next Tottenham game and population of Norway?"

Output:
[
  {{
    "id": "tottenham_next_match",
    "entity": "tottenham",
    "metric": "next_match"
  }},
  {{
    "id": "norway_population",
    "entity": "norway",
    "metric": "population"
  }}
]
"""

        response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

        output = response["message"]["content"]

        print("LLM raw response (requirements):", output)

        output = output.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(output)

            structured = []

            for req in parsed:

                structured.append({
                "id": req.get("id", ""),
                "entity": req.get("entity", ""),
                "metric": req.get("metric", ""),
                "answered": False,
                "answer": None
            })

            return structured

        except Exception as e:
            print("Requirement extraction failed:", e)

        return []

    
    def is_requirement_satisfied(self):

        req_entities = self.requirements.get("entities", [])

        for ent in req_entities:
            if ent not in self.state["entities"]:
                return False

        return True
    
    def extract_entities_llm(self, query):
        print("extract llm entities")
        prompt = f"""
    Extract ONLY the main real-world entities from this query.

    Query:
    {query}

    Return JSON:
    {{"entities": ["entity1", "entity2"]}}

    Rules:
    - Only include real entities (countries, cities, organizations)
    - Do NOT include verbs or generic words
    - Do NOT include metrics (like population, GDP, etc.)
    - Keep it minimal (max 3 entities)
    """

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        output = response["message"]["content"]
        print("LLM raw response (entities):", output)

        output = output.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(output)
            return [e.lower().strip() for e in parsed.get("entities", [])]
        except:
            return []
        
    
    def is_requirement_answered(self, requirement, result):

        print(f"Checking requirement: {requirement['id']}")

        if not result or result.strip() == "":
            return False

        bad_signals = [
            "no useful information",
            "access denied",
            "error"
        ]

        if any(bad in result.lower() for bad in bad_signals):
            return False

        prompt = f"""
    Requirement:
    Entity: {requirement["entity"]}
    Metric: {requirement["metric"]}

    Result:
    {result}

    Does this result DIRECTLY and SPECIFICALLY answer this requirement?

    Rules:

    - The result must answer THIS exact requirement
    - Related information is NOT enough
    - General descriptions are NOT enough
    - Partial matches are NOT enough
    - If the exact answer is present → YES
    - Otherwise → NO

    Examples:

    Requirement:
    Entity: norway
    Metric: population

    Result:
    "The population of Norway is 5.6 million."

    Answer:
    YES

    ---

    Requirement:
    Entity: norway
    Metric: population

    Result:
    "Norway is a Nordic country."

    Answer:
    NO

    Respond ONLY:
    YES or NO
    """

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        answer = response["message"]["content"].strip().upper()

        return answer.startswith("YES")
    

    def build_plan(self, query):
        
        print("Building a plan...")
        prompt = f"""
You are a planning engine.

Convert the user query into a structured execution plan.

User Query:
{query}

Return STRICT JSON ONLY (no explanation):

{{
  "steps": [
    {{"type": "fetch", "entity": "entity_name", "metric": "metric_name"}},
    {{"type": "compute", "operation": "operation_name", "args": ["arg1", "arg2"]}}
  ]
}}

Rules:

1. Allowed step types:
   - "fetch": retrieve data
   - "compute": perform calculation

2. For "fetch":
   - MUST include: entity, metric
   - metric = what data is needed (e.g., population, gdp, ceo)

3. For "compute":
   - MUST include: operation, args
   - args MUST reference fetched entities EXACTLY
   - DO NOT invent variables

4. Supported operations:
   - "percentage"
   - "difference"
   - "sum"
   - "average"
   - "comparison"

5. Ordering:
   - ALL fetch steps MUST come BEFORE compute
   - No duplicate steps

6. Keep steps minimal:
   - Do not add unnecessary steps
   - Only include what is needed

7. Output format rules:
   - JSON only
   - No markdown
   - No explanation
   - No text before or after JSON

---

Examples:

Query:
"What is the population of India?"

Output:
{{
  "steps": [
    {{"type": "fetch", "entity": "india", "metric": "population"}}
  ]
}}

Query:
"What % of India's population is China's?"

Output:
{{
  "steps": [
    {{"type": "fetch", "entity": "india", "metric": "population"}},
    {{"type": "fetch", "entity": "china", "metric": "population"}},
    {{"type": "compute", "operation": "percentage", "args": ["china", "india"]}}
  ]
}}

Query:
"Which country has higher GDP, India or China?"

Output:
{{
  "steps": [
    {{"type": "fetch", "entity": "india", "metric": "gdp"}},
    {{"type": "fetch", "entity": "china", "metric": "gdp"}},
    {{"type": "compute", "operation": "comparison", "args": ["india", "china"]}}
  ]
}}
"""
        response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

        text = response["message"]["content"]
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text).get("steps", [])
        except:
            return []