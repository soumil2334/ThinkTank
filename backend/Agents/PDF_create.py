from pydantic import BaseModel, Field
from langchain_core.tools import tool
from backend.Agents.Common_State import State
from backend.Agents.Search_Agent import search, get_webpage

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

class LLM1(BaseModel):
    Business_insights: str = Field(description="Key ideas about business model, value proposition, and overall viability.")
    Market_insights: str = Field(description="Insights about market demand, trends, competitors, and opportunities.")
    Technical_insights: str = Field(description="Key technical approaches, tools, constraints, and feasibility considerations.")
    Risks: str = Field(description="Potential challenges, uncertainties, or factors that could hinder success.")
    Action_items: str = Field(description="Concrete next steps or tasks identified from the discussion.")
    Decisions: str = Field(description="Clear conclusions or choices agreed upon during the discussion.")
    Open_questions: str = Field(description="Unresolved questions or areas needing further clarification.")
    Customer_insights: str = Field(description="Understanding of user needs, pain points, and target audience behavior.")
    Monetization_strategies: str = Field(description="Proposed ways to generate revenue or pricing models.")
    Growth_strategies: str = Field(description="Ideas for scaling, marketing, and expanding the product or business.")
    Priority_signals: str = Field(description="Most important or frequently emphasized ideas indicating team focus.")
    Knowledge_gaps: str = Field(description="Missing information or areas that require further research or validation.")

def Agent1(state : State)