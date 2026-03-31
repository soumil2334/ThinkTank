from typing import TypedDict, Annotated, Optional
import base64
from langgraph.graph.message import add_messages, BaseMessage

class State(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

    #LLM output for agent
    LLM_instruction : Optional[str]
    next : Optional[str]

    ## PDF
    pdf_bytes : Optional[bytes]
    pdf_base64 : Optional[str]
    PDF_feedback : Optional[str]
    Last_PDF_Agent_output : Optional[str] #feedback after HITL

    #Google Meet
    Meet_dict : Optional[dict]
    Meet_link : Optional[str]
    Meet_feedback : Optional[str]
    Last_Scheduler_Agent_output : Optional[str]

    #Email Agent
    sender_address : Optional[str]
    Email_Feedback: Optional[str]
    to_emails : Optional[list[str]]
    cc_emails : Optional[list[str]]
    bcc_emails : Optional[list[str]]
    subject : Optional[str]
    body : Optional[str]
    email_status : Optional[str]