from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
import os
import click
import random
import re
import json
from datetime import datetime
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
load_dotenv(override=True)

# Prompt Compression Functions
def compress_prompt(prompt: str, max_tokens: int = 8000) -> str:
    """
    Compress a prompt using multiple techniques to reduce token count.
    
    Args:
        prompt: Original prompt text
        max_tokens: Maximum token limit (default 8000 for safety)
    
    Returns:
        Compressed prompt text
    """
    # Step 1: Remove redundant whitespace and normalize
    compressed = re.sub(r'\s+', ' ', prompt.strip())
    
    # Step 2: Remove common redundant phrases
    redundant_patterns = [
        r'\b(please|kindly|would you|could you)\s+',
        r'\b(comprehensive|detailed|thorough|extensive)\s+',
        r'\b(analysis|report|intelligence)\s+(analysis|report|intelligence)',
        r'\b(provide|give|deliver)\s+(provide|give|deliver)',
        r'\b(including|containing|featuring)\s+(including|containing|featuring)',
    ]
    
    for pattern in redundant_patterns:
        compressed = re.sub(pattern, '', compressed, flags=re.IGNORECASE)
    
    # Step 3: Abbreviate common terms
    abbreviations = {
        'threat actor': 'TA',
        'techniques tactics and procedures': 'TTPs',
        'MITRE ATT&CK': 'ATT&CK',
        'comprehensive analysis': 'analysis',
        'detailed intelligence': 'intel',
        'associated with': 'linked to',
        'recommendations and': 'recs &',
        'defensive measures': 'defenses',
        'risk assessment': 'risk eval',
        'threat landscape': 'threat env',
        'operating systems': 'OS',
        'point of sale': 'POS',
        'initial access': 'IA',
        'lateral movement': 'LM',
        'persistence': 'persist',
        'privilege escalation': 'priv esc',
        'defense evasion': 'def evade',
        'credential access': 'cred access',
        'discovery': 'disc',
        'collection': 'collect',
        'command and control': 'C2',
        'exfiltration': 'exfil',
        'impact': 'impact'
    }
    
    for full_term, abbrev in abbreviations.items():
        compressed = re.sub(r'\b' + re.escape(full_term) + r'\b', abbrev, compressed, flags=re.IGNORECASE)
    
    # Step 4: Remove verbose connectors and filler words
    filler_words = [
        r'\b(in order to|so as to|for the purpose of)\s+',
        r'\b(it is important to note that|it should be noted that|it is worth noting that)\s+',
        r'\b(additionally|furthermore|moreover|in addition)\s+',
        r'\b(specifically|particularly|especially|notably)\s+',
        r'\b(however|nevertheless|nonetheless|on the other hand)\s+',
        r'\b(therefore|thus|hence|consequently)\s+',
    ]
    
    for pattern in filler_words:
        compressed = re.sub(pattern, '', compressed, flags=re.IGNORECASE)
    
    # Step 5: Compress lists and bullet points
    compressed = re.sub(r'-\s*', '• ', compressed)
    compressed = re.sub(r'\n\s*\n', '\n', compressed)
    
    # Step 6: Remove excessive punctuation
    compressed = re.sub(r'[.]{2,}', '.', compressed)
    compressed = re.sub(r'[!]{2,}', '!', compressed)
    
    return compressed.strip()

def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count (4 chars ≈ 1 token for English).
    This is a conservative estimate.
    """
    return len(text) // 4

def create_compressed_prompt(scenario_type: str, scenario: str) -> str:
    """
    Create a compressed, efficient prompt for the given scenario.
    """
    base_prompts = {
        "threat_actor_profiling": f"Analyze TA: {scenario}\n\nProvide: aliases, TTPs (ATT&CK table), malware/tools, campaigns, targets, timeline, defenses, risk eval",
        
        "malware_analysis": f"Analyze malware: {scenario}\n\nProvide: family/variants, capabilities, ATT&CK mapping (table), platforms, linked TAs, detection, defenses, risk eval",
        
        "campaign_investigation": f"Investigate campaign: {scenario}\n\nProvide: details/attribution, timeline, targets, TTPs (table), linked TAs/malware, impact, defenses",
        
        "navigator_layer_generation": f"Generate ATT&CK layer: {scenario}\n\nCreate: techniques with scoring, color coding, comments, examples, JSON file, metadata",
        
        "comparative_analysis": f"Compare: {scenario}\n\nProvide: side-by-side comparison, overlapping TTPs, unique characteristics, risk eval, ATT&CK layer, recommendations"
    }
    
    prompt = base_prompts.get(scenario_type, f"Analyze: {scenario}")
    
    # Apply compression
    compressed = compress_prompt(prompt)
    
    # Add intelligent guidance
    compressed += "\n\nINTELLIGENT APPROACH: Use targeted MCP queries. Avoid bulk data retrieval. Start specific, expand only if needed."
    
    return compressed

def create_compressed_task_description(scenario_type: str, scenario: str) -> str:
    """
    Create compressed task descriptions to reduce context length.
    """
    base_descriptions = {
        "threat_actor_profiling": f"Profile TA group: {scenario}",
        "malware_analysis": f"Analyze malware: {scenario}",
        "campaign_investigation": f"Investigate campaign: {scenario}",
        "navigator_layer_generation": f"Generate ATT&CK layer: {scenario}",
        "comparative_analysis": f"Compare entities: {scenario}"
    }
    
    return base_descriptions.get(scenario_type, f"Analyze: {scenario}")

def create_compressed_expected_output(scenario_type: str) -> str:
    """
    Create compressed expected output descriptions.
    """
    outputs = {
        "threat_actor_profiling": "TA intel: aliases, TTPs (table), malware/tools, campaigns, targets, timeline, defenses",
        "malware_analysis": "Malware intel: family, capabilities, ATT&CK mapping (table), platforms, TAs, detection, defenses",
        "campaign_investigation": "Campaign intel: details, timeline, targets, TTPs (table), TAs/malware, impact, defenses",
        "navigator_layer_generation": "ATT&CK layer JSON: techniques, scoring, colors, comments, examples, metadata",
        "comparative_analysis": "Comparative analysis: side-by-side, overlaps, unique traits, risk eval, ATT&CK layer"
    }
    
    return outputs.get(scenario_type, "Threat intel report with ATT&CK mapping")

def log_token_usage(text: str, context: str = ""):
    """
    Log token usage for monitoring and optimization.
    """
    token_count = estimate_tokens(text)
    print(f"🔍 Token usage - {context}: ~{token_count} tokens")
    
    if token_count > 10000:
        print(f"⚠️  High token usage detected: {token_count} tokens")
    elif token_count > 5000:
        print(f"📊 Moderate token usage: {token_count} tokens")
    else:
        print(f"✅ Low token usage: {token_count} tokens")
    
    return token_count

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
    """Generate a compressed, efficient prompt for the given scenario type and scenario."""
    return create_compressed_prompt(scenario_type, scenario)

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
            role="ATT&CK Threat Intel Analyst",
            goal="Analyze TAs, malware, techniques using ATT&CK framework efficiently.",
            backstory="""Expert cybersec analyst with deep ATT&CK knowledge. Specializes in TA profiling, malware analysis, technique mapping.
            
            INTELLIGENT APPROACH:
            - Understand token limits & context windows
            - Start with targeted queries, expand only if needed
            - Use most efficient MCP tools per task
            - Avoid bulk data retrieval unless required
            - Think strategically about data needs
            - Prioritize quality over quantity
            - Make smart trade-offs between comprehensiveness & efficiency""",
            llm=self.llm,
            tools=self.get_mcp_tools(),  # Get all available MCP tools
            verbose=VERBOSE,
            max_iter=MAX_ITER
        )

def create_tasks_with_prompts(prompts: dict, crew_instance, scenario_type: str):
    """Create tasks with compressed prompts to reduce context length."""
    mitre_analyst = crew_instance.mitre_analyst()
    
    # Get the scenario from the prompt
    scenario = list(prompts.values())[0] if prompts else "Unknown scenario"
    
    # Create compressed task description
    task_description = create_compressed_task_description(scenario_type, scenario)
    
    # Create compressed expected output
    expected_output = create_compressed_expected_output(scenario_type)
    
    # Add intelligent guidance for specific scenario types
    if scenario_type == "malware_analysis":
        task_description += "\n\nINTELLIGENT: Start with get_software_by_alias, then targeted technique queries. Avoid bulk data."
    elif scenario_type == "navigator_layer_generation":
        task_description += "\n\nINTELLIGENT: Use get_techniques_by_tactic, get_techniques_by_platform. Think strategically about relevance."
    
    task = Task(
        description=task_description,
        expected_output=expected_output,
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
    
    # Generate compressed prompt for the selected scenario type
    prompts = {scenario_type: generate_prompt(scenario_type, selected_scenario)}
    
    # Log token usage for monitoring
    prompt_text = prompts[scenario_type]
    log_token_usage(prompt_text, f"Compressed prompt for {scenario_type}")
    
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