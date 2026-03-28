from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage, SystemMessage
from backend.Agents.Common_State import State
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import os
load_dotenv()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')

llm=ChatOpenAI(api_key=OPENAI_API_KEY, model='gpt-4o-mini')

class Orchestration_Outline(BaseModel):
        next: str

async def Orchestrator_Agent(state : State):
        message=state['messages'][-1].content
        instruction=f'''You are an orchestrator agent. Your sole responsibility is to analyze the user's message and route it to the correct specialized agent.
        
## Available agents

1. Email_agent — user wants to send, draft, or compose an email
2. Meet_scheduler_agent — user wants to schedule a meeting, set up a call, or add an event to calendar
3. PDF_agent — user wants a summary, overview, or PDF export of the conversation
4. Search_agent — user wants to search the web or find external information
5. Task_assign_agent — user wants to break down a project, idea, or discussion into tasks
6. General_agent — user has a general query that does not match any of the above

## Rules
- Read the user message carefully and identify the primary intent.
- Route to exactly ONE agent — the one that best matches the intent.
- If the message is ambiguous, pick the closest match. Do not ask clarifying questions.
- Never explain your reasoning. Never add any text outside the JSON.
- Always respond in this exact format:

{"next": "<agent_name>"}

## Examples

User: "Can you email John the meeting notes?"
{"next": "Email_agent"}

User: "Set up a 30-minute sync with the design team tomorrow"
{"next": "Meet_scheduler_agent"}

User: "Give me a PDF summary of what we discussed"
{"next": "PDF_agent"}

User: "What is the latest on GPT-5?"
{"next": "Search_agent"}

User: "Break this idea into actionable tasks"
{"next": "Task_assign_agent"}

User: "What does idempotent mean?"
{"next": "General_agent"}'''
        
        model=ChatOpenAI(model='gpt-4o-mini')
        structure_llm=model.with_structured_output(Orchestration_Outline)
        response=structure_llm.invoke([SystemMessage(content=instruction), HumanMessage(content=message)])
        return {
                'messages' : [AIMessage(content=response.next)] ##Orchestration_Outline(next="Email_agent")
                                                                ##Need to return a list for add_message to work
        }