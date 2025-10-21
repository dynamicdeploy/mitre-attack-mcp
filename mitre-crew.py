from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
import os
import click
import random
from datetime import datetime
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
load_dotenv(override=True)
# Initialize LLM (only when needed)
def get_llm():
    """Get LLM instance with Ollama."""
   # return LLM(model="ollama/gemma3:4b", temperature=0.1, base_url="http://localhost:11434")
    return LLM(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.1)

# MITRE ATT&CK MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8032/mcp")
MAX_ITER = 3
VERBOSE = True
# Realistic synthetic prompts based on real threat intelligence scenarios
THREAT_INTELLIGENCE_SCENARIOS = {
    "threat_actor_profiling": [
        "APT29 (Cozy Bear) - Russian state-sponsored group targeting government and healthcare sectors",
        "Lazarus Group - North Korean threat actor known for cryptocurrency theft and destructive attacks",
        "FIN8 - Financially motivated group targeting point-of-sale systems in retail and hospitality",
        "APT1 (Comment Crew) - Chinese military unit 61398 targeting intellectual property",
        "Carbanak - Financially motivated group targeting banks and financial institutions",
        "Wizard Spider - Russian cybercriminal group behind TrickBot and Conti ransomware",
        "TA505 - Russian threat actor distributing banking trojans and ransomware",
        "APT28 (Fancy Bear) - Russian military intelligence targeting government and defense",
        "Maze Ransomware Group - Financially motivated ransomware-as-a-service operation",
        "REvil (Sodinokibi) - Russian ransomware group targeting high-value organizations"
    ],
    "malware_analysis": [
        "TrickBot - Banking trojan evolved into modular malware platform",
        "Emotet - Banking trojan and botnet used for credential theft and malware distribution",
        "Ryuk Ransomware - Targeted ransomware used in high-impact attacks",
        "Cobalt Strike - Commercial penetration testing tool abused by threat actors",
        "Mimikatz - Credential dumping tool used for lateral movement",
        "PowerShell Empire - Post-exploitation framework for persistence and lateral movement",
        "QakBot (Qbot) - Banking trojan and botnet for credential theft",
        "IcedID - Banking trojan used as initial access vector for ransomware",
        "BazarLoader - Malware loader used to deploy ransomware",
        "Conti Ransomware - Ransomware-as-a-service targeting critical infrastructure"
    ],
    "campaign_investigation": [
        "SolarWinds Supply Chain Attack - Russian APT29 campaign targeting government and tech companies",
        "Colonial Pipeline Ransomware Attack - DarkSide ransomware targeting critical infrastructure",
        "Kaseya VSA Supply Chain Attack - REvil ransomware targeting MSPs and their customers",
        "Microsoft Exchange Server Hafnium Campaign - Chinese APT targeting email servers",
        "NotPetya Cyber Attack - Russian military operation targeting Ukraine with global impact",
        "WannaCry Ransomware Campaign - North Korean Lazarus Group targeting healthcare and government",
        "ShadowPad Backdoor Campaign - Chinese APT targeting software supply chains",
        "Olympic Destroyer - Russian operation targeting Winter Olympics infrastructure",
        "Triton/Trisis - Iranian APT targeting industrial control systems",
        "CloudHopper Campaign - Chinese APT targeting managed service providers"
    ],
    "navigator_layer_generation": [
        "Create layer for healthcare sector threats - Focus on ransomware and data theft",
        "Generate financial sector threat layer - Banking trojans and fraud techniques",
        "Build energy sector attack layer - ICS/SCADA targeting and critical infrastructure",
        "Create government sector threat layer - APT techniques and espionage",
        "Generate education sector layer - Ransomware and data breach techniques",
        "Build manufacturing sector layer - Supply chain and industrial targeting",
        "Create retail sector threat layer - POS malware and payment card theft",
        "Generate technology sector layer - Supply chain and intellectual property theft",
        "Build transportation sector layer - Critical infrastructure and operational disruption",
        "Create defense contractor layer - Advanced persistent threats and espionage"
    ],
    "comparative_analysis": [
        "Compare APT29 vs APT28 - Russian state-sponsored groups and their techniques",
        "Analyze TrickBot vs Emotet - Banking trojans and their evolution",
        "Compare Ryuk vs Conti - Ransomware groups and their targeting",
        "Analyze Lazarus vs Carbanak - North Korean vs Russian threat actors",
        "Compare Maze vs REvil - Ransomware-as-a-service operations",
        "Analyze FIN8 vs TA505 - Financially motivated Russian groups",
        "Compare SolarWinds vs Kaseya - Supply chain attack campaigns",
        "Analyze WannaCry vs NotPetya - Destructive malware campaigns",
        "Compare healthcare vs financial targeting - Sector-specific attack patterns",
        "Analyze government vs critical infrastructure - State-sponsored targeting"
    ]
}

def save_analysis_to_markdown(result, scenario_type: str, scenario: str, output_dir: str = "analysis_outputs"):
    """Save the analysis result to a markdown file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_scenario = "".join(c for c in scenario if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_scenario = safe_scenario.replace(' ', '_')[:50]  # Limit length
    filename = f"{timestamp}_{scenario_type}_{safe_scenario}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create markdown content
    markdown_content = f"""# MITRE ATT&CK Threat Intelligence Analysis

## Analysis Details
- **Analysis Type**: {scenario_type.replace('_', ' ').title()}
- **Scenario**: {scenario}
- **Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **MCP Server**: {MCP_SERVER_URL}

## Analysis Results

{result}

---
*Generated by MITRE ATT&CK Threat Intelligence Analysis Tool*
"""
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filepath

def generate_prompt(scenario_type: str, scenario: str) -> str:
    """Generate a detailed prompt for the given scenario type and scenario."""
    
    if scenario_type == "threat_actor_profiling":
        return f"""Analyze the threat actor group: {scenario}
        
Provide comprehensive intelligence including:
- Group aliases, attribution, and evolution timeline
- Complete TTP analysis mapped to MITRE ATT&CK techniques
- Associated malware, tools, and software used
- Campaigns attributed to this group
- Target sectors, platforms, and organizations
- Attack patterns and methodology
- Defensive recommendations and mitigations
- Risk assessment and threat landscape positioning"""

    elif scenario_type == "malware_analysis":
        return f"""Conduct detailed analysis of the malware: {scenario}
        
Provide comprehensive malware intelligence including:
- Malware family overview, variants, and evolution
- Capabilities, functionality, and attack vectors
- MITRE ATT&CK technique mapping and procedures
- Target platforms, operating systems, and applications
- Associated threat actor groups and campaigns
- Detection signatures and behavioral indicators
- Mitigation strategies and defensive measures
- Risk assessment and threat landscape impact"""

    elif scenario_type == "campaign_investigation":
        return f"""Investigate the campaign: {scenario}
        
Provide comprehensive campaign intelligence including:
- Campaign details, aliases, and attribution
- Timeline, evolution, and attack phases
- Target sectors, organizations, and geographic regions
- Techniques, tactics, and procedures (TTPs) used
- Associated threat actor groups and malware
- Attack vectors and initial access methods
- Impact assessment and damage evaluation
- Defensive recommendations and lessons learned"""

    elif scenario_type == "navigator_layer_generation":
        return f"""Generate MITRE ATT&CK Navigator layer for: {scenario}
        
Create a comprehensive Navigator layer including:
- All relevant techniques with appropriate scoring
- Color coding for different threat levels or categories
- Detailed comments explaining technique usage
- Real-world examples and procedure descriptions
- Layer metadata and description
- Downloadable JSON file for ATT&CK Navigator
- Strategic recommendations based on the layer"""

    elif scenario_type == "comparative_analysis":
        return f"""Perform comparative analysis of: {scenario}
        
Provide comprehensive comparative intelligence including:
- Side-by-side comparison of selected entities
- Overlapping techniques and common TTPs
- Unique characteristics and differentiators
- Similarities and differences in targeting
- Risk assessment and threat landscape positioning
- MITRE ATT&CK Navigator layer showing overlaps and differences
- Strategic recommendations based on comparative analysis"""

    else:
        return f"Analyze the following scenario: {scenario}"

@CrewBase
class MitreThreatIntelligenceCrew:
    """MITRE ATT&CK Threat Intelligence Crew with MCP integration."""
    
    # MCP Server configuration
    mcp_server_params = [
        {
            "url": MCP_SERVER_URL,
            "transport": "streamable-http"
        }
    ]
    
    # Connection timeout (optional)
    mcp_connect_timeout = 30
    
    def __init__(self):
        self.llm = get_llm()
    
    @agent
    def mitre_analyst(self):
        """Create MITRE ATT&CK Threat Intelligence Agent with MCP tools."""
        return Agent(
            role="MITRE ATT&CK Threat Intelligence Analyst",
            goal="Analyze threat actors, malware, and techniques using MITRE ATT&CK framework.",
            backstory="""Expert cybersecurity analyst with deep knowledge of the MITRE ATT&CK framework and the ability to provide comprehensive analysis of threat actors, malware, and techniques.
            You specialize in threat actor profiling, malware analysis, and technique mapping. You have extensive knowledge of the MITRE ATT&CK framework and can provide detailed threat intelligence analysis.
            
            You are an INTELLIGENT analyst who makes smart decisions about data usage:
            - You understand token limits and context windows
            - You start with targeted queries and expand only when necessary
            - You use the most efficient MCP tools for each specific task
            - You avoid bulk data retrieval unless absolutely required
            - You think strategically about what data is actually needed
            - You prioritize quality over quantity in your analysis
            - You make intelligent trade-offs between comprehensiveness and efficiency""",
            llm=self.llm,
            tools=self.get_mcp_tools(),  # Get all available MCP tools
            verbose=VERBOSE,
            max_iter=MAX_ITER
        )

def create_tasks_with_prompts(prompts: dict, crew_instance, scenario_type: str):
    """Create tasks with dynamic prompts based on user selection."""
    mitre_analyst = crew_instance.mitre_analyst()
    
    # Only create the task for the selected scenario type
    if scenario_type == "threat_actor_profiling":
        task = Task(
            description=prompts.get("threat_actor_profiling", "Perform comprehensive threat actor group analysis."),
            expected_output="""Comprehensive threat actor intelligence report covering:
            1. Group information, aliases, and attribution
            2. Detailed TTP analysis mapped to MITRE ATT&CK techniques
            3. Associated malware and tools used
            4. Campaigns attributed to the group
            5. Target sectors and platforms
            6. Timeline and evolution analysis
            7. Defensive recommendations and mitigations""",
            agent=mitre_analyst
        )
    elif scenario_type == "malware_analysis":
        task = Task(
            description=prompts.get("malware_analysis", "Conduct comprehensive malware and software analysis.") + 
            "\n\nINTELLIGENT APPROACH: Start with specific malware queries (get_software_by_alias) then get related techniques. Use targeted searches, not bulk data retrieval.",
            expected_output="""Detailed malware intelligence report including:
            1. Malware family overview and variants
            2. Capabilities and functionality analysis
            3. MITRE ATT&CK technique mapping
            4. Target platforms and operating systems
            5. Associated threat actor groups
            6. Detection and mitigation recommendations
            7. Risk assessment and threat landscape positioning""",
            agent=mitre_analyst
        )
    elif scenario_type == "campaign_investigation":
        task = Task(
            description=prompts.get("campaign_investigation", "Investigate specific campaigns and their characteristics."),
            expected_output="""Campaign intelligence report covering:
            1. Campaign details, aliases, and attribution
            2. Timeline and evolution analysis
            3. Target sectors and organizations
            4. Techniques and software used
            5. Associated threat actor groups
            6. Campaign-specific TTP analysis
            7. Defensive recommendations and mitigations""",
            agent=mitre_analyst
        )
    elif scenario_type == "navigator_layer_generation":
        task = Task(
            description=prompts.get("navigator_layer_generation", "Generate MITRE ATT&CK Navigator layers for threat intelligence.") + 
            "\n\nINTELLIGENT APPROACH: Think strategically about what techniques are relevant to the scenario. Use targeted queries (get_techniques_by_tactic, get_techniques_by_platform) rather than bulk retrieval. Be smart about data usage.",
            expected_output="""MITRE ATT&CK Navigator layer JSON file with:
            1. All relevant techniques with appropriate scoring
            2. Color coding for different categories or threat levels
            3. Detailed comments explaining technique usage
            4. Real-world examples and procedure descriptions
            5. Downloadable JSON file for ATT&CK Navigator
            6. Layer metadata and description""",
            agent=mitre_analyst
        )
    elif scenario_type == "comparative_analysis":
        task = Task(
            description=prompts.get("comparative_analysis", "Perform comparative analysis between threat actors, malware, or campaigns."),
            expected_output="""Comparative analysis report including:
            1. Side-by-side comparison of selected entities
            2. Overlapping techniques and common TTPs
            3. Unique characteristics and differentiators
            4. Risk assessment and threat landscape positioning
            5. MITRE ATT&CK Navigator layer showing overlaps and differences
            6. Strategic recommendations based on comparative analysis""",
            agent=mitre_analyst
        )
    else:
        # Fallback for unknown scenario types
        task = Task(
            description=prompts.get(scenario_type, "Perform comprehensive threat intelligence analysis."),
            expected_output="""Comprehensive threat intelligence report including:
            1. Detailed analysis of the specified scenario
            2. MITRE ATT&CK technique mapping
            3. Associated threat actors and tools
            4. Risk assessment and recommendations
            5. Defensive strategies and mitigations""",
            agent=mitre_analyst
        )

    return [task]



def display_scenarios():
    """Display all available scenarios in a formatted way."""
    click.echo("\n🎯 Available Threat Intelligence Scenarios:")
    click.echo("=" * 60)
    
    for category, scenarios in THREAT_INTELLIGENCE_SCENARIOS.items():
        click.echo(f"\n📋 {category.replace('_', ' ').title()}:")
        for i, scenario in enumerate(scenarios):
            click.echo(f"  {i}: {scenario}")
    
    click.echo(f"\n💡 Total scenarios available: {sum(len(scenarios) for scenarios in THREAT_INTELLIGENCE_SCENARIOS.values())}")

def interactive_selection():
    """Interactive scenario selection with Click's built-in features."""
    click.echo("\n🎯 MITRE ATT&CK Threat Intelligence Analysis Tool")
    click.echo("=" * 60)
    click.echo("Welcome to the interactive threat intelligence analysis tool!")
    click.echo("This tool will guide you through selecting analysis scenarios.\n")
    
    # Step 1: Choose analysis type
    click.echo("📋 Step 1: Choose Analysis Type")
    click.echo("-" * 30)
    
    categories = list(THREAT_INTELLIGENCE_SCENARIOS.keys())
    category_choices = []
    
    for i, category in enumerate(categories):
        display_name = category.replace('_', ' ').title()
        category_choices.append((display_name, category))
        click.echo(f"  {i}: {display_name}")
    
    scenario_type = click.prompt(
        "\nSelect analysis type",
        type=click.Choice([str(i) for i in range(len(categories))]),
        show_choices=True
    )
    scenario_type = categories[int(scenario_type)]
    
    click.echo(f"\n✅ Selected: {scenario_type.replace('_', ' ').title()}")
    
    # Step 2: Choose scenario or custom
    click.echo(f"\n📋 Step 2: Choose {scenario_type.replace('_', ' ').title()} Scenario")
    click.echo("-" * 40)
    
    scenarios = THREAT_INTELLIGENCE_SCENARIOS[scenario_type]
    
    # Display scenarios with better formatting
    for i, scenario in enumerate(scenarios):
        click.echo(f"  {i}: {scenario}")
    
    click.echo(f"\nOptions:")
    click.echo(f"  • Enter a number (0-{len(scenarios)-1}) to select a scenario")
    click.echo(f"  • Enter 'custom' to provide your own scenario")
    click.echo(f"  • Enter 'random' to select a random scenario")
    
    while True:
        choice = click.prompt(f"\nYour choice", type=str).lower().strip()
        
        if choice == 'custom':
            custom_scenario = click.prompt("Enter your custom scenario description")
            return scenario_type, None, custom_scenario
            
        elif choice == 'random':
            scenario_index = random.randint(0, len(scenarios) - 1)
            selected_scenario = scenarios[scenario_index]
            click.echo(f"\n🎲 Random selection: {selected_scenario}")
            return scenario_type, scenario_index, None
            
        elif choice.isdigit():
            scenario_index = int(choice)
            if 0 <= scenario_index < len(scenarios):
                selected_scenario = scenarios[scenario_index]
                click.echo(f"\n✅ Selected: {selected_scenario}")
                return scenario_type, scenario_index, None
            else:
                click.echo(f"❌ Invalid number. Please enter 0-{len(scenarios)-1}")
        else:
            click.echo("❌ Invalid choice. Please enter a number, 'custom', or 'random'")

def confirm_analysis(scenario_type, selected_scenario):
    """Confirm the analysis parameters before proceeding."""
    click.echo(f"\n🔍 Analysis Configuration")
    click.echo("=" * 30)
    click.echo(f"Analysis Type: {scenario_type.replace('_', ' ').title()}")
    click.echo(f"Scenario: {selected_scenario}")
    click.echo(f"MCP Server: {MCP_SERVER_URL}")
    
    if not os.getenv("OPENAI_API_KEY"):
        click.echo("⚠️  Warning: OPENAI_API_KEY not set - analysis will fail")
    
    return click.confirm("\n🚀 Proceed with analysis?", default=True)

@click.command()
@click.option('--scenario-type', 
              type=click.Choice(['threat_actor_profiling', 'malware_analysis', 'campaign_investigation', 
                               'navigator_layer_generation', 'comparative_analysis']),
              help='Type of threat intelligence analysis to perform')
@click.option('--scenario-index', 
              type=int, 
              help='Index of the scenario to use (0-9)')
@click.option('--custom-scenario', 
              type=str, 
              help='Custom scenario description')
@click.option('--list-scenarios', 
              is_flag=True, 
              help='List all available scenarios')
@click.option('--interactive', 
              is_flag=True, 
              help='Run in interactive mode with guided prompts')
@click.option('--output-dir', 
              type=str, 
              default='analysis_outputs',
              help='Directory to save markdown output files (default: analysis_outputs)')
def main(scenario_type, scenario_index, custom_scenario, list_scenarios, interactive, output_dir):
    """MITRE ATT&CK Threat Intelligence Analysis Tool"""
    
    if list_scenarios:
        display_scenarios()
        return
    
    # Interactive mode or no parameters provided
    if interactive or not scenario_type:
        scenario_type, scenario_index, custom_scenario = interactive_selection()
    
    # Determine the scenario to use
    if custom_scenario:
        selected_scenario = custom_scenario
    else:
        if scenario_index is None:
            scenario_index = 0  # Default to first scenario
        scenarios = THREAT_INTELLIGENCE_SCENARIOS[scenario_type]
        if not (0 <= scenario_index < len(scenarios)):
            click.echo("❌ Invalid scenario index")
            return
        selected_scenario = scenarios[scenario_index]
    
    # Confirm analysis before proceeding
    if not confirm_analysis(scenario_type, selected_scenario):
        click.echo("👋 Analysis cancelled by user")
        return
    
    # Generate prompt only for the selected scenario type
    prompts = {scenario_type: generate_prompt(scenario_type, selected_scenario)}
    
    # Create and execute crew using simple DSL integration
    click.echo(f"\n🚀 Starting MITRE ATT&CK threat intelligence analysis...")
    click.echo(f"📡 Using MCP server at: {MCP_SERVER_URL}")
    click.echo(f"🎯 Primary scenario: {selected_scenario}")
    click.echo("=" * 50)
    
    try:
        # Create crew instance with MCP integration
        crew_instance = MitreThreatIntelligenceCrew()
        
        # Create tasks with dynamic prompts
        tasks = create_tasks_with_prompts(prompts, crew_instance, scenario_type)
        
        # Create and execute crew
        mitre_crew = Crew(
            agents=[crew_instance.mitre_analyst()],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        result = mitre_crew.kickoff()
        print(result)
        
        # Save results to markdown file
        output_file = save_analysis_to_markdown(result, scenario_type, selected_scenario, output_dir)
        
        click.echo(f"\n✅ MITRE ATT&CK analysis completed successfully!")
        click.echo(f"📊 Analysis results: {result}")
        click.echo(f"📄 Results saved to: {output_file}")
    except Exception as e:
        click.echo(f"\n❌ Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()