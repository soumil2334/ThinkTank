from typing import TypedDict, Annotated, cast
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage, SystemMessage
from backend.Agents.Common_State import State
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import datetime
import pdfkit
import base64
import uuid
import os
import json
load_dotenv()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')

llm=ChatOpenAI(api_key=OPENAI_API_KEY, model='gpt-4o-mini')


def image_to_base64(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].replace('.', '')
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/{ext};base64,{encoded}"


def Report(conversation : State, image_path : str='./pdf_image.png'):
    
    LLM_instruction = conversation['LLM_instruction']
    
    Last_Output=conversation.get('Last_PDF_Agent_output', '')
    feedback=conversation.get('PDF_feedback', "")
    conversation_text=''
    for message in conversation['messages']:
        if isinstance(message, HumanMessage):
            role = "human"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"
        elif isinstance(message, ToolMessage):
            role = "tool"
        else:
            role = "unknown"
            
        conversation_text += f"{role}: {message.content}\n\n"

    image_b64=image_to_base64(image_path=image_path)

    instruction=f'''
You are an expert analyst and report generator.

Your task is to read a conversation between participants (which may include brainstorming, discussion, or idea exploration) and convert it into a structured, insight-rich report — NOT just a summary.

You must extract meaningful conclusions, reasoning, and actionable insights, then generate a clean HTML document that will later be converted into a PDF.
------------------------
FEEDBACK
------------------------
If there was a previous generation for this same task which was not satisfactory to the user, a feedback has been provided
Feedback : {feedback} for output : {Last_Output}
If the feedback is empty ignore it
------------------------
INPUT
------------------------
You will be given:
1. A list of messages (conversation)
2. A base64-encoded background image: {image_b64}

------------------------
PART 1 — ANALYSIS
------------------------

Carefully analyze the conversation and extract:

1. Final Decision(s)
   - What was ultimately concluded?

2. Key Ideas & Concepts
   - Core idea
   - Supporting ideas
   - Variations explored

3. Argument Mapping
   - Main claims
   - Supporting reasoning
   - Counterarguments (if any)

4. Action Plan
   - Tasks
   - Responsible person (if mentioned)
   - Priority (High/Medium/Low)

5. Insights & Learnings
   - General principles or lessons derived

6. Risks & Gaps
   - Missing considerations
   - Potential risks
   - Unresolved questions

7. Agreements & Disagreements
   - What participants agreed on
   - What remained debated

8. Evolution of Thought (optional but preferred)
   - How the discussion progressed step-by-step

IMPORTANT RULES:
- Do NOT summarize line-by-line
- Focus on high-value insights and structure
- Be concise but meaningful
- Do NOT include raw conversation text unless necessary

------------------------
PART 2 — HTML GENERATION
------------------------

Generate a COMPLETE HTML document that presents the above analysis as a professional report.

STRICT REQUIREMENTS:

- Use this exact base64 string as the background:
  {image_b64}

- Place background using a `position: fixed` div so it repeats on every page

- Page layout:
  - A4 width: 794px
  - Allow natural vertical flow (no fixed height)

- Spacing constraints:
  - Leave at least 80px space at the TOP (no content there)
  - Leave at least 80px space at the BOTTOM

- Add a semi-transparent overlay behind text to ensure readability over the background

- Typography:
  - Clean, modern, professional
  - Clear section hierarchy (headings, subheadings)

- Structure the report using sections:
  - Title (e.g., "Conversation Insight Report")
  - Date / metadata
  - Each analysis section clearly separated

- Use:
  - Headings (h1, h2, h3)
  - Bullet points where appropriate
  - Clean spacing and alignment

- The HTML must be directly usable with PDF tools (like wkhtmltopdf)

------------------------
OUTPUT RULES
------------------------

- Return ONLY valid HTML
- Do NOT include explanations
- Do NOT include markdown
- Do NOT include JSON
- Output must start with <!DOCTYPE html>

------------------------
GOAL
------------------------

Transform an unstructured conversation into:
→ a decision-ready report  
→ visually clean PDF-ready HTML  
→ insight-rich, structured output  

This is not summarization — this is intelligent analysis + presentation.
'''
    response=llm.invoke([SystemMessage(content=instruction), AIMessage(content=LLM_instruction), HumanMessage(content=conversation_text)])
    html=response.content.strip()
    
    options = {
        'page-size': 'A4',
        'margin-top': '0',
        'margin-right': '0',
        'margin-bottom': '0',
        'margin-left': '0',
        'encoding': 'UTF-8',
        'enable-local-file-access': '',
    }
    pdf=cast(bytes,pdfkit.from_string(input=html, output_path=False, options=options))    
    return pdf, html


def PDF_Agent(state: State):
    pdf_bytes, html = Report(conversation=state)
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return {
        "pdf_bytes": pdf_bytes,
        "pdf_base64": pdf_base64,
        "messages": [
            AIMessage(content="PDF generated. Please review.")
        ],
        'Last_PDF_Agent_output': html
        }


def review_pdf(state: State):
    response = interrupt({
        "type": "Review PDF",
        "pdf": state["pdf_base64"]
    })

    if isinstance(response, dict):
        decision = response.get("decision")
        feedback = response.get("feedback")
    else:
        decision = response
        feedback = None

    if decision == "approve":
        return Command(goto=END, update={'Last_PDF_Agent_output': None, 'pdf_bytes': None, 'pdf_feedback' : None})
    
    return Command(
        goto="PDF_Agent",
        update={"PDF_feedback": feedback}
    )
