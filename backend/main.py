from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.Graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from backend.Agents.Common_State import State
from langgraph.types import Command, interrupt
import sqlite3

class WebSocket_Manager:
    def __init__(self) -> None:
        self.active_websocket_clients=[]

    async def Connect(self, websocket : WebSocket):
        await websocket.accept()
        self.active_websocket_clients.append(websocket)

    def disconnect(self, websocket : WebSocket):
        self.active_websocket_clients.remove(websocket)

    async def broadcast(self, message : dict):
        for conn in self.active_websocket_clients:
            await conn.send_json(message)

app=FastAPI()
manager=WebSocket_Manager()

config={'configurable' : {'thread_id' : 'ThinkTank'}}
checkpointer=SqliteSaver.from_conn_string('checkpoints.db')

graph=build_graph(checkpointer)

@app.websocket('/ws')
async def Websocket_Chat(websocket : WebSocket):
    await manager.Connect(websocket=websocket)

    is_it_command=False

    try:
        while True:
            #receiving message from websocket client
            data = await websocket.receive_json()
            if not is_it_command:
                username= data.get('username', 'Anonymous')
                user_message = data.get('text')
            
            #displaying this message to all the other websocket clients
                await manager.broadcast(
                {
                    'role' : 'human',
                    'username' : username,
                    'text' : user_message
                })

                defined_state = {
                "messages": [HumanMessage(content=user_message)],
                'sender_address' : 'soumil2433@gmail.com',
                'members_list' :  [{'username' : 'soumil22', 'member_role': 'AI Engineer'}, {'username' : 'soumilsinha1', 'member_role': 'Backend Developer'},{'username' : 'soumil13', 'member_role': 'Marketing'},{'username' : 'soumilsinha18', 'member_role': 'Manager'}],
                'board_name' :  'My Trello board'}

                result = graph.invoke(defined_state)

                if "__interrupt__" in result:
                    interrupt_data = result["__interrupt__"]["value"]
                
                    type_agent= interrupt_data.get('type')
                    await manager.broadcast({
                        "type": "interrupt",
                        "subtype": type_agent,
                        "data": interrupt_data})
                    is_it_command=True
                    continue

                else : 
                    await manager.broadcast(
                        {
                            'role' : 'Ai',
                            'text' : result.get('messages')[-1].content
                        }
                    )
                    continue
            
            else:
                data_response=data.get('response')
                result_after=graph.invoke(Command(resume=data_response), config=config)

                if "__interrupt__" in result_after:
                    interrupt_data = result_after["__interrupt__"]["value"]

                    await manager.broadcast({
                        "type": "interrupt",
                        "subtype": interrupt_data.get('type'),
                        "data": interrupt_data
                    })

                    is_it_command = True
                    continue
                
                await manager.broadcast(
                        {   
                            'role' : 'AI',
                            'messages' : result_after.get('messages')[-1].content
                        }
                    )
                is_it_command = False   
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)