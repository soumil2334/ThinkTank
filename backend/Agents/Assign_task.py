from backend.Agents.Common_State import State
from pydantic import BaseModel,Field
from langgraph.types import Command, interrupt  
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('TRELLO_API')
TOKEN = os.getenv('TRELLO_TOKEN')


class checklist_item(BaseModel):
    name: str = Field(
        description="A short, actionable subtask (should be specific and executable)")

class checklist(BaseModel):
    name: str = Field(
        description="Title of the checklist grouping related subtasks")
    items: List[checklist_item] = Field(
        description="List of subtasks under this checklist")

class card(BaseModel):
    name: str = Field(
        description="Title of the task")
    assignee: str = Field(
        description="Trello member ID assigned to this task")
    description: str = Field(
        description="Detailed explanation of what needs to be done")
    checklists: List[checklist] = Field(
        description="Breakdown of the task into smaller steps")
    due_date: str = Field(
        description="Deadline in ISO format (YYYY-MM-DDTHH:MM:SSZ), or empty string if none")

class Card_List(BaseModel):
    name: str = Field(
        description="Stage or phase of the project (e.g., To Do, Backend, Testing)")
    cards: List[card] = Field(
        description="Tasks belonging to this phase")

class Boards(BaseModel):
    Board_name: str = Field(
        description="Name of the overall project board")
    lists: List[Card_List] = Field(
        description="All workflow stages and their tasks")
    

def Extract_tasks(state : State):
    conversation_history = ''

    messages = state['messages']
    for message in messages:
        if isinstance(message, HumanMessage):
            conversation_history+= f"Role : Human, Content : {message.content}\n"
        if isinstance(message, AIMessage):
            conversation_history+= f"Role : Assistant, Content : {message.content}\n"
        if isinstance(message, SystemMessage):
            conversation_history+= f"Role : System , Content : {message.content}\n"
        if isinstance(message, ToolMessage):
            conversation_history+= f"Role : Tool Call, Content : {message.content}\n"
    
    members=state['members_list']
    members_info=''

    for member in members:
        members_info+=f""" Name : {member.get('member_name')}, 
                           Role : {member.get('member_role')},
                           Member Trello_id : {member.get('member_trello')} \n"""

    system_instruction = f"""
You are a project planning assistant.

Your task is to analyze a conversation and convert it into a structured Trello board plan.

If there was a previous generation of the Trello board plan and the user has rejected the result:
Feedback : {state.get('Board_feedback', '')} For Output : {state.get('board_outline', )}

You must:
1. Extract the project goal
2. Break it into logical phases (lists)
3. Break phases into tasks (cards)
4. Break tasks into subtasks (checklists)
5. Assign each task to the most suitable team member using their role
6. Add a short, clear description for each task
7. Add due dates only if explicitly mentioned or strongly implied

---

You are given:

1. Conversation history (brainstorming discussion)
2. Team member details:
   - Name
   - Role
   - Trello Member ID

---

Assignment rules:
- Match task requirements with member roles
- Assign ONLY using the provided Trello member_id
- If no clear match, leave member_id as an empty string ""

---

Checklist rules:
- Break each task into small, actionable steps
- Each checklist item should be atomic (can be done in 1–2 hours)

---

Output rules:
- Output ONLY valid JSON
- Follow the schema exactly
- Do NOT include explanations
- Do NOT include extra fields
- Do NOT generate IDs (except member_id which is provided)
- Keep names concise and meaningful

---

Schema to follow:

{
  "Board_name": str,
  "lists": [
    {
      "name": str,
      "cards": [
        {
          "name": str,
          "assignee": str = '',
          "description": str,
          "due_date": str = '',
          "checklists": [
            {
              "name": str,
              "items": [
                {"name": str}
              ]
            }
          ]
        }
      ]
    }
  ]
}

"""
    human_instruction=f"""
Brainstorming discussion : {conversation_history}

Team Information : {members_info}
"""
    llm = ChatOpenAI(model='gpt-4o-mini')
    llm=llm.with_structured_output(Boards)
    response=llm.invoke([SystemMessage(content=system_instruction), HumanMessage(content=human_instruction)])
    
    return {
        'board_name' : response.Board_name,
        'board_outline' : response
    }

def human_review(state : State):
    response=interrupt({
        'type' : 'Board review',
        'Board_Name' : state['board_name'],
        'Board_Outline' : state['board_outline']
    })
    changes = response.Board_Outline # if only minor changes
    approval = response.status # if start agent again
    feedback = response.feedback

    if approval=='approved':
        return Command(
            goto='Create Board',
            update={
                'board_outline' : changes
            }
        )
    
    if approval=='rejected':
        return Command(
            goto='Extract Tasks',
            update={
                'Board_feedback' : feedback
            }
        )

def create_board(name):
    url = "https://api.trello.com/1/boards/"
    
    params = {
        "name": name,
        "defaultLists": "true",
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.post(url, params=params)
    return response.json()

def create_list(board_id, list_name):
    url = "https://api.trello.com/1/lists"
    
    params = {
        "name": list_name,
        "idBoard": board_id,
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.post(url, params=params)
    return response.json()

def create_card(list_id, title, description=""):
    url = "https://api.trello.com/1/cards"
    
    params = {
        "idList": list_id,
        "name": title,
        "desc": description,   # 👈 add description here
        "key": API_KEY,
        "token": TOKEN
    }

    return requests.post(url, params=params).json()


BASE_URL = "https://api.trello.com/1"

def create_checklist(card_id, checklist_name):
    url = f"{BASE_URL}/checklists"
    
    params = {
        "idCard": card_id,
        "name": checklist_name,
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.post(url, params=params)
    return response.json()

def add_checklist_item(checklist_id, item_name):
    url = f"{BASE_URL}/checklists/{checklist_id}/checkItems"
    
    params = {
        "name": item_name,
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.post(url, params=params)
    return response.json()

def assign_member(card_id, member_id):
    url = f"https://api.trello.com/1/cards/{card_id}/idMembers"
    
    params = {
        "value": member_id,
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.post(url, params=params)
    return response.json()

def set_due_date(card_id, due_date):
    url = f"https://api.trello.com/1/cards/{card_id}"
    
    params = {
        "due": due_date,
        "key": API_KEY,
        "token": TOKEN
    }

    response = requests.put(url, params=params)
    return response.json()


def Trello_agent(state:State):
    board_outline=state['board_outline']
    
    if not board_outline.Board_name:
        raise Exception("Board name missing")

    board_name=board_outline.Board_name

    Trello_board=create_board(board_name)

    Trello_board_id=Trello_board.get('id')

    Lists=board_outline.lists

    for lst in Lists:
        lst_name=lst.name

        Trello_lst=create_list(board_id=Trello_board_id, list_name=lst_name)

        Trello_list_id=Trello_lst.get('id')

        cards=lst.cards

        for card in cards:
            card_name=card.name
            card_desc=card.description
            card_assignee_id=card.assignee
            card_due_date=card.due_date


            Trello_card=create_card(Trello_list_id, card_name, description = card_desc)

            Trello_card_id=Trello_card.get('id')
             
            if card_due_date:
                set_due_date(Trello_card_id, card_due_date)

            if card_assignee_id:
                assign_member(Trello_card_id, card_assignee_id)

            checklists=card.checklists

            for Checklist in checklists:
                checklist_name=Checklist.name

                Trello_checklist=create_checklist(Trello_card_id, checklist_name)

                Trello_checklist_id=Trello_checklist.get('id')

                Checklist_items=Checklist.items

                for item in Checklist_items:
                    item_name=item.name

                    Trello_item = add_checklist_item(Trello_checklist_id, item_name)

    return {
        'board_id' : Trello_board_id
    }




    
    