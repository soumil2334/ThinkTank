from backend.Agents.Common_State import State

def Pass_AI(state:State):
    user_message=state.get('messages', '')
    words=str(user_message).strip().split(' ')
    ai_trigger_bool='CHAT'
    if '@AI' or '@Ai' or '@ai' in words:
        ai_trigger_bool='AI'

    return ai_trigger_bool

def orchestrator_function(state : State):
    next=state.get('next', '')
    return str(next)

