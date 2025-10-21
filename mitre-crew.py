from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Create agent with multiple MCP sources
multi_source_agent = Agent(
    role="Multi-Source Research Analyst",
    goal="Conduct comprehensive research using multiple data sources",
    backstory="""Expert researcher with access to web search, weather data,
    financial information, and academic research tools""",
    llm=llm,
    mcps=[
        # External MCP servers
        "https://mcp.exa.ai/mcp?api_key=your_exa_key&profile=research",
        "https://weather.api.com/mcp#get_current_conditions",

        # CrewAI AMP marketplace
        "crewai-amp:financial-insights",
        "crewai-amp:academic-research#pubmed_search",
        "crewai-amp:market-intelligence#competitor_analysis"
    ]
)

# Create comprehensive research task
research_task = Task(
    description="""Research the impact of AI agents on business productivity.
    Include current weather impacts on remote work, financial market trends,
    and recent academic publications on AI agent frameworks.""",
    expected_output="""Comprehensive report covering:
    1. AI agent business impact analysis
    2. Weather considerations for remote work
    3. Financial market trends related to AI
    4. Academic research citations and insights
    5. Competitive landscape analysis""",
    agent=multi_source_agent
)

# Create and execute crew
research_crew = Crew(
    agents=[multi_source_agent],
    tasks=[research_task],
    process=Process.sequential,
    verbose=True
)

result = research_crew.kickoff()
print(f"Research completed with {len(multi_source_agent.mcps)} MCP data sources")