from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.Graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from backend.Agents.Common_State import State
from langgraph.types import Command
import sqlite3


class ConnectionManager:  
    def __init__(self):  
        self.active_connections = []  

    async def connect(self, websocket):  
        await websocket.accept()  
        self.active_connections.append(websocket)  

    def disconnect(self, websocket):  
        self.active_connections.remove(websocket)  

    async def broadcast(self, message: dict):  
        for conn in self.active_connections:  
            await conn.send_json(message)

app = FastAPI()
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    config = {"configurable": {"thread_id": "global_room"}}
    checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
    graph=build_graph(checkpointer)

    try:
        while True:
            data = await websocket.receive_json()

            user_message = data["message"]
            username = data.get("user", "Anonymous")  

            await manager.broadcast({
                "type": "human",
                "user": username,
                "message": user_message
            })
            defined_state ={
                "messages": [HumanMessage(content=user_message)],
                'sender_address' : 'soumil2433@gmail.com',
                'members_list' :  [{'username' : 'soumil22', 'member_role': 'AI Engineer'}, {'username' : 'soumilsinha1', 'member_role': 'Backend Developer'},{'username' : 'soumil13', 'member_role': 'Marketing'},{'username' : 'soumilsinha18', 'member_role': 'Manager'}],
                'board_name' :  'My Trello board'
            }
             
            result = await graph.ainvoke(defined_state)
            
            
            if isinstance(result, Command):
                await manager.broadcast({
                    "type": "system",
                    "message": "Waiting for human input..."
                })
                continue

            ai_msg = result["messages"][-1]

            
            if ai_msg["role"] == "ai":
                await manager.broadcast({
                    "type": "ai",
                    "user": "AI",
                    "message": ai_msg["content"]
                })
                        