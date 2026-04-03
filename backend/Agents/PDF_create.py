from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import List, Optional
from backend.Agents.Common_State import State
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from backend.Agents.Search_Agent import search, get_webpage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import base64
import os

load_dotenv()


class Design(BaseModel):

@tool
def search_tool(query: str):
    """
    PURPOSE:
    Fetch external web information.

    WHEN TO USE:
    When external data or validation is needed.

    WHEN NOT TO USE:
    When insights can be derived from the discussion.

    INPUT:
    query (str): Specific search query.

    OUTPUT:
    dict: Relevant results with sources and snippets.

    USAGE:
    Extract key facts and integrate into insights.
    """
    search_dict=search(query=query)
    web_search_result=get_webpage(query, search_dict)

    return web_search_result


class DataPoint(BaseModel):
    label: str = Field(description="Category or segment name.")
    value: float = Field(description="Numerical value representing the category.")


class Visualization(BaseModel):
    type: str = Field(description="Type of visualization: pie_chart, bar_chart, line_chart, or table.")
    title: str = Field(description="Title of the visualization.")


class Insight(BaseModel):
    text: str = Field(description="Concise statement of the key insight.")
    importance: str = Field(description="Priority level of the insight: low, medium, or high.")
    supporting_points: Optional[List[str]] = Field(
        description="Short supporting points or reasoning behind the insight.")
    data_points: Optional[List[DataPoint]] = Field(
        description="Structured data used for visualization, if applicable.")
    visualization: Optional[Visualization] = Field(
        description="Suggested visualization for this insight, if useful.")
    chart_path: Optional[str] = None 


class Agent1Output(BaseModel):
    Business_insights: List[Insight] = Field(
        description="Insights related to business model, value proposition, and viability.")
    Market_insights:List[Insight] = Field(
        description="Insights about market demand, trends, competitors, and opportunities.")
    Technical_insights: List[Insight] = Field(
        description="Insights on technology choices, feasibility, and constraints.")
    Risks: List[Insight] = Field(
        description="Potential risks, challenges, or uncertainties identified.")
    Action_items: List[Insight] = Field(
        description="Concrete next steps or tasks derived from the discussion.")
    Decisions: List[Insight] = Field(
        description="Decisions or conclusions agreed upon by the team.")
    Open_questions: List[Insight] = Field(
        description="Unresolved questions requiring further discussion or research.")
    Customer_insights: List[Insight] = Field(
        description="Insights about user needs, pain points, and behavior.")
    Monetization_strategies: List[Insight] = Field(
        description="Proposed revenue models or pricing strategies.")
    Growth_strategies: List[Insight] = Field(
        description="Ideas for scaling, marketing, and expansion.")
    Priority_signals: List[Insight] = Field(
        description="Key ideas that were emphasized, repeated, or strongly agreed upon.")
    Knowledge_gaps: List[Insight] = Field(
        description="Missing information or areas needing validation or research.")


def Agent1(state : State):
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
    
    prompt=f'''
You are an Insight Extraction Agent.

Task:
Analyze a list of team messages and extract structured insights.

---

Extract insights under:
- Business_insights
- Market_insights
- Technical_insights
- Risks
- Action_items
- Decisions
- Open_questions
- Customer_insights
- Monetization_strategies
- Growth_strategies
- Priority_signals
- Knowledge_gaps

---

Output:
Return ONLY valid JSON matching the schema.

Each insight must include:
- text (concise statement)
- importance (low | medium | high)

Optional:
- supporting_points (short bullets)
- data_points: [{label, value}] if numerical info is present
- visualization: {type, title} ONLY if useful

---

Visualization rules:
- pie_chart → proportions
- bar_chart → comparisons/frequency
- line_chart → trends
- table → structured comparison
- avoid unnecessary charts

---

Tool: search_tool(query)

Use ONLY if:
- external data is required (market, competitors, trends)
- discussion lacks real-world context

Do NOT use if:
- insights come from discussion
- task is summarization/structuring

Constraints:
- max 1–2 calls
- use specific queries
- do not include raw results
- integrate only relevant facts

---

Rules:
- no hallucinations
- no repetition
- keep concise
- prioritize clarity
- most insights should come from discussion

---

Messages:
{conversation_history}
'''
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')

    llm=ChatOpenAI(model='gpt-4o-mini')
    llm_with_tool=llm.bind_tools([search_tool])
    llm_structure=llm.with_structured_output(Agent1Output)

    response=llm_structure.invoke([HumanMessage(content=prompt)])

    return {
        "Agent1Output" : response
    }

class Agent2Output(BaseModel):
    html: str = Field(description="Complete HTML document string for the report. Must be valid, self-contained, and ready for rendering or PDF conversion.")

def inject_font_html(font_path: str) -> str:
    with open(font_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

    font_b64 = font_to_base64('./Helvetica.ttf')

    font_face = f"""
    <style>
      @font-face {{
        font-family: 'Inter';
        src: url('data:font/truetype;base64,{font_b64}');
      }}
    </style>"""

    html = html.replace("</head>", f"{font_face}</head>")
    return html


def Agent2(state : State):
    respomse_agent1=state['Agent1Output']

    instruction = f"""
    You are a Report Generation Agent.

Your task is to convert structured insights (JSON input) into a professional HTML report.

---

OUTPUT RULES:

- Return ONLY valid HTML (no markdown, no explanations)
- Output must be a complete HTML document:
  - <html>, <head>, <body>
- Use clean, readable structure with headings and sections
- Use semantic tags (<h1>, <h2>, <p>, <ul>, etc.)
- Keep styling minimal and inline or in <style> tag

---

CONTENT INSTRUCTIONS:

- Convert each insight category into sections:
  - Executive Summary
  - Business Insights
  - Market Insights
  - Technical Insights
  - Risks
  - Customer Insights
  - Monetization Strategy
  - Growth Strategy
  - Action Plan
  - Open Questions
  - Knowledge Gaps

- Expand insights into concise paragraphs
- Use bullet points where useful
- Prioritize high-importance insights

-Content should be in 
---

VISUALIZATION HANDLING:

If "chart_path" is present:
Insert:
<img src="{chart_path}" alt="{visualization.title}" />

If chart_path is missing but visualization exists:
Insert placeholder:
<div>[Insert {type}: {title}]</div>
---

BACKGROUND IMAGE (IMPORTANT):

- Add support for a background image using base64
- Use CSS like:

  body {
    background-image: url("data:image/png;base64,{{background_image}}");
    background-size: cover;
    background-repeat: no-repeat;
  }

- Keep {{background_image}} as a placeholder (DO NOT replace it)

---

STRICT RULES:

- Do NOT add explanations
- Do NOT output JSON
- Do NOT hallucinate new information
- Only use provided insights

---

INPUT JSON:
{{agent1_output}}
    """

