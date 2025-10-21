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

# Import embedding libraries
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Note: FAISS and RetrievalQA imports removed as they're not used in the current implementation
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/mitre-crew-embedding.log")

# Initialize LLM (only when needed)
def get_llm():
    """Get LLM instance with Ollama."""
   # return LLM(model="ollama/gemma3:4b", temperature=0.1, base_url="http://localhost:11434")
    return LLM(
        model="gpt-4o-mini", 
        api_key=os.getenv("OPENAI_API_KEY"), 
        temperature=0.1,
        max_tokens=2000,  # Limit output tokens to reduce context
        timeout=30,  # Reduce timeout to prevent long waits
        top_p=0.9  # Add top_p for better response quality
    )

# MITRE ATT&CK MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8032/mcp")
MAX_ITER = 3
VERBOSE = True

# Initialize embedding model (local, no API key required)
def get_embedding_model():
    """Get local embedding model for context compression."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},  # Use CPU (or 'cuda' if you have GPU)
        encode_kwargs={'normalize_embeddings': True}
    )

# Context compression functions
def compress_context_with_embeddings(text, query, max_length=400):
    """Compress context using embeddings and similarity to query."""
    try:
        logger.info(f"Starting embedding compression: {len(text)} chars -> target: {max_length} chars")
        
        # Initialize embedding model
        embeddings = get_embedding_model()
        
        # Split text into smaller chunks for better compression
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=150,  # Much smaller chunks
            chunk_overlap=25  # Minimal overlap
        )
        chunks = text_splitter.split_text(text)
        
        logger.info(f"Split into {len(chunks)} chunks")
        
        if len(chunks) <= 1:
            logger.info("Only one chunk, truncating directly")
            return text[:max_length]
        
        # Get embeddings for chunks and query
        logger.info("Generating embeddings...")
        chunk_embeddings = embeddings.embed_documents(chunks)
        query_embedding = embeddings.embed_query(query)
        
        # Calculate similarities
        similarities = []
        for chunk_emb in chunk_embeddings:
            similarity = np.dot(chunk_emb, query_embedding) / (
                np.linalg.norm(chunk_emb) * np.linalg.norm(query_embedding)
            )
            similarities.append(similarity)
        
        # Get most relevant chunks
        chunk_scores = list(zip(chunks, similarities))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Top similarity scores: {[f'{score:.3f}' for _, score in chunk_scores[:3]]}")
        
        # FORCE compression by selecting only top chunks that fit in max_length
        compressed_text = ""
        selected_chunks = 0
        target_compression = max_length  # Force aggressive compression
        
        for chunk, score in chunk_scores:
            # Only add if it fits AND we haven't reached target
            if len(compressed_text) + len(chunk) <= target_compression:
                compressed_text += chunk + "\n\n"
                selected_chunks += 1
            else:
                # If adding this chunk would exceed limit, stop
                break
        
        # If still too long, truncate the last chunk
        if len(compressed_text) > target_compression:
            compressed_text = compressed_text[:target_compression]
        
        logger.info(f"Selected {selected_chunks} chunks, final length: {len(compressed_text)} chars")
        compression_ratio = len(compressed_text) / len(text) * 100
        logger.info(f"Compression achieved: {compression_ratio:.1f}% of original")
        
        return compressed_text.strip()
        
    except Exception as e:
        logger.error(f"Embedding compression failed: {e}")
        # Fallback to simple truncation
        return text[:max_length]

def compress_context_with_tfidf(text, query, max_sentences=5):
    """Compress context using TF-IDF similarity."""
    try:
        logger.info(f"Starting TF-IDF compression: {len(text)} chars -> max {max_sentences} sentences")
        
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        logger.info(f"Split into {len(sentences)} sentences")
        
        if len(sentences) <= max_sentences:
            logger.info("Not enough sentences to compress")
            return text
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences + [query])
        
        # Calculate similarity to query
        query_vector = tfidf_matrix[-1]
        similarities = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
        
        # Get most relevant sentences
        sentence_scores = list(zip(sentences, similarities))
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Top TF-IDF similarity scores: {[f'{score:.3f}' for _, score in sentence_scores[:3]]}")
        
        # Select top sentences (more aggressive)
        selected_sentences = [s[0] for s in sentence_scores[:max_sentences]]
        result = '. '.join(selected_sentences) + '.'
        
        logger.info(f"TF-IDF compression result: {len(result)} chars")
        return result
        
    except Exception as e:
        logger.error(f"TF-IDF compression failed: {e}")
        # Fallback to simple truncation
        return text[:1000]  # More aggressive fallback

def create_compressed_task_description(scenario_type: str, scenario: str) -> str:
    """Create a compressed task description using embeddings."""
    # Get the original prompt
    original_prompt = generate_prompt(scenario_type, scenario)
    logger.info(f"Original prompt length: {len(original_prompt)} chars")
    
    # Create a query for compression
    query = f"{scenario_type} {scenario}"
    
    # Try embedding-based compression first (more aggressive target)
    try:
        logger.info(f"Trying embedding-based compression: {len(original_prompt)} chars")
        compressed_prompt = compress_context_with_embeddings(original_prompt, query, max_length=200)  # Even more aggressive
        compression_ratio = len(compressed_prompt) / len(original_prompt) * 100
        logger.info(f"✅ Used embedding-based compression: {len(compressed_prompt)} chars ({compression_ratio:.1f}% of original)")
        return compressed_prompt
    except Exception as e:
        logger.error(f"⚠️ Embedding compression failed: {e}")
        # Fallback to TF-IDF compression
        try:
            logger.info(f"Trying TF-IDF compression: {len(original_prompt)} chars")
            compressed_prompt = compress_context_with_tfidf(original_prompt, query, max_sentences=1)  # Even more aggressive
            compression_ratio = len(compressed_prompt) / len(original_prompt) * 100
            logger.info(f"✅ Used TF-IDF compression: {len(compressed_prompt)} chars ({compression_ratio:.1f}% of original)")
            return compressed_prompt
        except Exception as e2:
            logger.error(f"⚠️ TF-IDF compression failed: {e2}")
            # Final fallback to simple truncation (very aggressive)
            logger.error("⚠️ Using simple truncation fallback")
            fallback = original_prompt[:150]  # Even more aggressive fallback
            logger.info(f"Fallback truncation: {len(fallback)} chars")
            return fallback

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
    
    # Create dynamic title based on analysis type and scenario
    if scenario_type == "threat_actor_profiling":
        title = f"Threat Actor Profiling: {scenario}"
    elif scenario_type == "malware_analysis":
        title = f"Malware Analysis: {scenario}"
    elif scenario_type == "campaign_investigation":
        title = f"Campaign Investigation: {scenario}"
    elif scenario_type == "navigator_layer_generation":
        title = f"Navigator Layer Generation: {scenario}"
    elif scenario_type == "comparative_analysis":
        title = f"Comparative Analysis: {scenario}"
    else:
        title = f"MITRE ATT&CK Analysis: {scenario}"
    
    # Create markdown content
    markdown_content = f"""# {title}

## Analysis Details
- **Analysis Type**: {scenario_type.replace('_', ' ').title()}
- **Scenario**: {scenario}
- **Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **MCP Server**: {MCP_SERVER_URL}
- **Optimization Method**: Intelligent content filtering

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
        return f"""Create a comprehensive MITRE ATT&CK Navigator layer analysis for: {scenario}
        
Provide a detailed analysis report including:
- Layer purpose and strategic objectives
- Selected techniques with detailed rationale and scoring
- Technique categorization by threat level and relevance
- Real-world examples and use cases for each technique
- Strategic recommendations and implementation guidance
- Layer implementation guidance for ATT&CK Navigator
- Next steps and follow-up actions"""

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
    """MITRE ATT&CK Threat Intelligence Crew with MCP integration and embedding compression."""
    
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
        self.embedding_model = get_embedding_model()
    
    @agent
    def mitre_analyst(self):
        """Create MITRE ATT&CK Threat Intelligence Agent with MCP tools and embedding compression."""
        return Agent(
            role="MITRE ATT&CK Threat Intelligence Analyst",
            goal="Analyze threat actors, malware, and techniques using MITRE ATT&CK framework with intelligent context compression.",
            backstory="""Expert cybersecurity analyst with deep knowledge of the MITRE ATT&CK framework and the ability to provide comprehensive analysis of threat actors, malware, and techniques.
            You specialize in threat actor profiling, malware analysis, and technique mapping. You have extensive knowledge of the MITRE ATT&CK framework and can provide detailed threat intelligence analysis.
            
            You are an INTELLIGENT analyst who makes smart decisions about data usage:
            - You understand token limits and context windows (CRITICAL: Stay under 150,000 tokens total)
            - You start with targeted queries and expand only when necessary
            - You use the most efficient MCP tools for each specific task
            - You avoid bulk data retrieval unless absolutely required
            - You think strategically about what data is actually needed
            - You prioritize quality over quantity in your analysis
            - You make intelligent trade-offs between comprehensiveness and efficiency
            - You LIMIT your queries to 3-5 specific techniques maximum per analysis
            - You focus on the most relevant techniques rather than comprehensive coverage
            - You use targeted searches (get_techniques_by_tactic, get_software_by_alias) instead of bulk retrieval
            - You avoid get_all_* functions that return massive datasets
            - You use embedding-based context compression to optimize analysis efficiency""",
            llm=self.llm,
            tools=self.get_mcp_tools(),  # Get all available MCP tools
            verbose=VERBOSE,
            max_iter=MAX_ITER,
            respect_context_window=True,
            inject_date = True
        )

def create_tasks_with_prompts(prompts: dict, crew_instance, scenario_type: str):
    """Create tasks with dynamic prompts based on user selection and embedding compression."""
    mitre_analyst = crew_instance.mitre_analyst()
    
    # Only create the task for the selected scenario type
    if scenario_type == "threat_actor_profiling":
        task = Task(
            description=prompts.get("threat_actor_profiling", "Perform comprehensive threat actor group analysis."),
            expected_output="""Comprehensive threat actor intelligence report covering:
            1. Group information, aliases, and attribution
            2. Detailed TTP analysis mapped to MITRE ATT&CK techniques (format as table with columns: Technique ID, Name, Description)
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
            "\n\nCRITICAL TOKEN LIMIT: You must stay under 150,000 total tokens. Use ONLY 3-5 most relevant techniques. Start with specific malware queries (get_software_by_alias) then get related techniques. Use targeted searches, not bulk data retrieval.",
            expected_output="""Detailed malware intelligence report including:
            1. Malware family overview and variants
            2. Capabilities and functionality analysis
            3. MITRE ATT&CK technique mapping (format as table with columns: Technique ID, Name, Description)
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
            4. Techniques and software used (format techniques as table with columns: Technique ID, Name, Description)
            5. Associated threat actor groups
            6. Campaign-specific TTP analysis
            7. Defensive recommendations and mitigations""",
            agent=mitre_analyst
        )
    elif scenario_type == "navigator_layer_generation":
        task = Task(
            description=prompts.get("navigator_layer_generation", "Generate MITRE ATT&CK Navigator layers for threat intelligence.") + 
            "\n\nCRITICAL TOKEN LIMIT: You must stay under 150,000 total tokens. Use ONLY 3-5 most relevant techniques. Use targeted queries (get_techniques_by_tactic, get_techniques_by_platform) rather than bulk retrieval. Focus on quality over quantity.",
            expected_output="""Comprehensive Navigator Layer Analysis Report including:
            1. Layer overview and purpose
            2. Selected techniques with rationale (format as table with columns: Technique ID, Name, Score, Rationale)
            3. Technique categorization and threat levels
            4. Real-world examples and use cases
            5. Strategic recommendations based on the layer
            6. Layer implementation guidance for ATT&CK Navigator
            7. Next steps and follow-up actions""",
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
    click.echo("🧠 Context Optimization: Intelligent content filtering enabled")
    
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
    
    # Generate prompt with embedding compression
    logger.info(f"Starting analysis for scenario: {selected_scenario}")
    original_prompt = generate_prompt(scenario_type, selected_scenario)
    logger.info(f"Generated original prompt: {len(original_prompt)} chars")
    
    compressed_prompt = create_compressed_task_description(scenario_type, selected_scenario)
    compression_ratio = len(compressed_prompt) / len(original_prompt) * 100
    logger.info(f"Final compression: {len(compressed_prompt)} chars ({compression_ratio:.1f}% of original)")
    logger.info(f"Compressed prompt: {compressed_prompt}")
    
    # Create prompts dictionary with compressed content
    prompts = {scenario_type: compressed_prompt}
    
    # Add aggressive context management instructions
    context_instructions = """
    
    CRITICAL TOKEN LIMIT MANAGEMENT:
    - Maximum 150,000 tokens total (you're currently at risk of exceeding this)
    - Use ONLY 3-5 most relevant techniques maximum
    - Focus on quality over quantity
    - Use targeted queries, avoid bulk data retrieval
    - If you hit token limits, prioritize the most critical information
    """
    
    # Add context instructions to all prompts
    for key in prompts:
        prompts[key] = prompts[key] + context_instructions
    
    # Create and execute crew using simple DSL integration
    click.echo(f"\n🚀 Starting MITRE ATT&CK threat intelligence analysis...")
    click.echo(f"📡 Using MCP server at: {MCP_SERVER_URL}")
    click.echo(f"🎯 Primary scenario: {selected_scenario}")
    click.echo(f"🧠 Context optimization: {len(compressed_prompt)} chars (original: {len(original_prompt)} chars) - {compression_ratio:.1f}% reduction")
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
        
        # Log usage metrics
        try:
            usage_metrics = mitre_crew.usage_metrics
            logger.info(f"Usage metrics: {usage_metrics}")
            
            click.echo(f"\n📊 Usage Metrics:")
            click.echo(f"  • Prompt tokens: {usage_metrics.prompt_tokens}")
            click.echo(f"  • Completion tokens: {usage_metrics.completion_tokens}")
            click.echo(f"  • Total tokens: {usage_metrics.total_tokens}")
            click.echo(f"  • Cached prompt tokens: {usage_metrics.cached_prompt_tokens}")
            click.echo(f"  • Successful requests: {usage_metrics.successful_requests}")
            
            # Log detailed metrics
            logger.info(f"Detailed usage metrics:")
            logger.info(f"  - Prompt tokens: {usage_metrics.prompt_tokens}")
            logger.info(f"  - Completion tokens: {usage_metrics.completion_tokens}")
            logger.info(f"  - Total tokens: {usage_metrics.total_tokens}")
            logger.info(f"  - Cached prompt tokens: {usage_metrics.cached_prompt_tokens}")
            logger.info(f"  - Successful requests: {usage_metrics.successful_requests}")
            
        except Exception as e:
            logger.warning(f"Could not retrieve usage metrics: {e}")
            click.echo(f"\n📊 Usage Metrics: Could not retrieve metrics - {e}")
        
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
