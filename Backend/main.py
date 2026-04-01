from fastapi import FastAPI
from pydantic import BaseModel
from Backend.agent import Agent

class QueryRequest(BaseModel):
    query:str 

# creating an object of agent class
first_agent=Agent()
app=FastAPI()

@app.post("/run-agent")
def run_agent(request: QueryRequest):
    result=first_agent.run(request.query)
    return {"response": result}
    
