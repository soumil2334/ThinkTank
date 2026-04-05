from backend.Agents.Common_State import State
from backend.Agents.Assign_task import Board_members_list, Extract_tasks, human_review, Trello_agent
from backend.Agents.Email_agent import Email_agent, review_node, send_email
from backend.Agents.general_agent import general_agent
from backend.Agents.Meet_scheduler_agent import Scheduler_Agent, create_meeting, review_meeting
from backend.Agents.PDF_create import Agent1, Agent2
from backend.Agents.Search_Agent import Search_agent
from backend.Agents.Orchestrator_Agent import Orchestrator_Agent
from backend.Agents.Chat_only import human_chat
from langgraph.graph.state import StateGraph, START, END
builder=StateGraph(State)

#Chat Only
builder.add_node('Chat_Only', human_chat)

#Main Agent - Orchestratr agent
builder.add_node('Orchestrator', Orchestrator_Agent)

#Assign tasks - trello
builder.add_node('Get_Members', Board_members_list)
builder.add_node('Extract_Tasks', Extract_tasks)
builder.add_node('HITL_Trello', human_review)
builder.add_node('Trello', Trello_agent)

#Email 
builder.add_node('Email_Content', Email_agent)
builder.add_node('HITL_Email', review_node)
builder.add_node('Send_Email', send_email)

# general 
builder.add_node('General', general_agent)

#Google meet scheduler
builder.add_node('Schedule_Meeting', Scheduler_Agent)
builder.add_node('Create_Meet', create_meeting)
builder.add_node('HITL_Meet', review_meeting)

#PDF or report
builder.add_node('PDF_Report', Agent1)
builder.add_node('PDF_create', Agent2)

#Search Web
builder.add_node('Search', Search_agent)




