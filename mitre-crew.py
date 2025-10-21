from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import ChatOpenAI
import os
import click
import random
from crewai_tools import MCPServerAdapter
# Initialize LLM (only when needed)
def get_llm():
    """Get LLM instance with Ollama."""
    return LLM(model="ollama/gemma3:4b", temperature=0.1, base_url="http://localhost:11434")

# MITRE ATT&CK MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8032/mcp")
server_params = {
    "url": MCP_SERVER_URL,
    "transport": "streamable-http"
}
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

def create_mitre_analyst(mcp_tools):
    """Create MITRE ATT&CK Threat Intelligence Agent with dynamic LLM."""
    llm = get_llm()
    if llm is None:
        raise click.ClickException("❌ Cannot create agent without LLM. Please set OPENAI_API_KEY environment variable.")
    
    return Agent(
        role="MITRE ATT&CK Threat Intelligence Analyst",
        goal="Analyze threat actors, malware, and techniques using MITRE ATT&CK framework.",
        backstory="""Expert cybersecurity analyst with deep knowledge of the MITRE ATT&CK framework and the ability to use the MITRE ATT&CK data to provide a comprehensive analysis of the threat actor, malware, and techniques.
        You specialize in threat actor profiling, malware analysis, and technique mapping.""",
        llm=llm,
        tools=mcp_tools,
        verbose=True
    )

def create_tasks_with_prompts(prompts: dict, mitre_analyst:Agent):
    """Create tasks with dynamic prompts based on user selection."""
   # mitre_analyst = create_mitre_analyst()
    
    threat_actor_profiling_task = Task(
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

    malware_analysis_task = Task(
        description=prompts.get("malware_analysis", "Conduct comprehensive malware and software analysis."),
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

    campaign_investigation_task = Task(
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

    navigator_layer_generation_task = Task(
        description=prompts.get("navigator_layer_generation", "Generate MITRE ATT&CK Navigator layers for threat intelligence."),
        expected_output="""MITRE ATT&CK Navigator layer JSON file with:
        1. All relevant techniques with appropriate scoring
        2. Color coding for different categories or threat levels
        3. Detailed comments explaining technique usage
        4. Real-world examples and procedure descriptions
        5. Downloadable JSON file for ATT&CK Navigator
        6. Layer metadata and description""",
        agent=mitre_analyst
    )

    comparative_analysis_task = Task(
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

    return [
        threat_actor_profiling_task,
        malware_analysis_task,
        campaign_investigation_task,
        navigator_layer_generation_task,
        comparative_analysis_task
    ]

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
def main(scenario_type, scenario_index, custom_scenario, list_scenarios, interactive):
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
    
    # Generate prompts for all task types
    prompts = {}
    for task_type in THREAT_INTELLIGENCE_SCENARIOS.keys():
        if task_type == scenario_type:
            prompts[task_type] = generate_prompt(task_type, selected_scenario)
        else:
            # Use a random scenario from other categories for variety
            random_scenario = random.choice(THREAT_INTELLIGENCE_SCENARIOS[task_type])
            prompts[task_type] = generate_prompt(task_type, random_scenario)
    
    # Create tasks with dynamic prompts
   


    # Create and execute crew
    with MCPServerAdapter(server_params, connect_timeout=60) as mcp_tools:
        print(f"Available tools: {[tool.name for tool in mcp_tools]}")
        mitre_analyst = create_mitre_analyst(mcp_tools)
        tasks = create_tasks_with_prompts(prompts, mitre_analyst)
        
        mitre_crew = Crew(
            agents=[mitre_analyst],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

    click.echo(f"\n🚀 Starting MITRE ATT&CK threat intelligence analysis...")
    click.echo(f"📡 Using MCP server at: {MCP_SERVER_URL}")
    click.echo(f"🎯 Primary scenario: {selected_scenario}")
    click.echo("=" * 50)
    
    try:
        result = mitre_crew.kickoff()
        click.echo(f"\n✅ MITRE ATT&CK analysis completed successfully!")
        click.echo(f"📊 Analysis results: {result}")
    except Exception as e:
        click.echo(f"\n❌ Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()