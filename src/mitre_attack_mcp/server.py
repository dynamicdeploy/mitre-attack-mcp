from typing import Any, Dict, List
import os, json, argparse, re, sys
import traceback
import signal
import threading
import time

from mitreattack.stix20 import MitreAttackData
from mitreattack.navlayers.manipulators.layerops import LayerOps
from mitreattack.navlayers.core.layer import Layer
from mitreattack.navlayers import UsageLayerGenerator
from mitreattack.navlayers import ToSvg, SVGConfig
from mitreattack.navlayers import ToExcel
from mitreattack import download_stix, release_info
from fastmcp import FastMCP
# from mcp.server.fastmcp import FastMCP
from hd_logging import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file_path="logs/server.log")


DEFAULT_DATA_DIR_NAME = "mitre-attack-data"

# Initialize FastMCP server
mcp = FastMCP("mitre-attack")

# Dictionary to store MitreAttackData objects for each domain
attack_data_sources: Dict[str, MitreAttackData] = {}

# Global flag for graceful shutdown
shutdown_requested = False


def download_stix_data(data_path):
    """Download STIX data for all domains.

    This function:
    1. Downloads STIX data for enterprise, mobile, and ics domains
    2. Places all JSON files directly in the specified data_path directory

    Args:
        data_path: Path to directory where STIX files should be downloaded.

    Returns:
        List[str]: A list of tuples containing (domain, file_path) for each downloaded STIX file
    """
    logger.info(f"Starting STIX data download to: {data_path}")
    domains = ["enterprise", "mobile", "ics"]
    stix_file_paths = []

    try:
        # Create the data directory if it doesn't exist
        if not os.path.exists(data_path):
            logger.info(f"Creating data directory: {data_path}")
            os.makedirs(data_path)
        else:
            logger.debug(f"Data directory already exists: {data_path}")

        # Download STIX data for each domain
        for domain in domains:
            logger.info(f"Downloading STIX data for domain: {domain}")
            try:
                # Get release information
                releases = release_info.STIX21[domain]
                known_hash = releases[release_info.LATEST_VERSION]
                logger.debug(f"Using release {release_info.LATEST_VERSION} for {domain} with hash: {known_hash}")

                # Download STIX data directly to the target path
                download_stix.download_stix(
                    stix_version="2.1",
                    domain=domain,
                    download_dir=data_path,
                    release=release_info.LATEST_VERSION,
                    known_hash=known_hash,
                )

                # Save path to the downloaded file
                domain_key = f"{domain}-attack"
                stix_path = os.path.join(data_path, f"{domain_key}.json")
                stix_file_paths.append((domain, stix_path))
                logger.info(f"Successfully downloaded {domain} data to: {stix_path}")

            except Exception as e:
                logger.error(f"Failed to download STIX data for domain {domain}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

        logger.info(f"Successfully downloaded STIX data for all domains. Files: {stix_file_paths}")
        return stix_file_paths

    except Exception as e:
        logger.error(f"Critical error in download_stix_data: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def load_stix_data(data_path):
    """Load all STIX data files from the specified directory into the attack_data_sources dictionary.

    Args:
        data_path: Path to the directory containing the STIX JSON files
    """
    logger.info(f"Loading STIX data from: {data_path}")
    domains = ["enterprise", "mobile", "ics"]
    loaded_domains = []

    try:
        for domain in domains:
            domain_key = f"{domain}-attack"
            stix_path = os.path.join(
                data_path, "v" + release_info.LATEST_VERSION, f"{domain_key}.json"
            )
            logger.debug(f"Looking for {domain} data at: {stix_path}")

            # Check if the file exists before loading
            if os.path.exists(stix_path):
                logger.info(f"Loading {domain} data from: {stix_path}")
                try:
                    attack_data_sources[domain_key] = MitreAttackData(stix_path)
                    loaded_domains.append(domain)
                    logger.info(f"Successfully loaded {domain} data")
                except Exception as e:
                    logger.error(f"Failed to load {domain} data from {stix_path}: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"STIX data file not found for {domain}: {stix_path}")

        logger.info(f"Successfully loaded STIX data for domains: {loaded_domains}")
        return loaded_domains

    except Exception as e:
        logger.error(f"Critical error in load_stix_data: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


# Function to get the appropriate MitreAttackData object for a domain
def get_attack_data(domain: str = "enterprise") -> MitreAttackData:
    """Get the MitreAttackData object for the specified domain.

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')

    Returns:
        MitreAttackData object for the specified domain
    """
    logger.debug(f"Getting attack data for domain: {domain}")
    domain_key = f"{domain}-attack"

    try:
        # Check if domain data is loaded
        if domain_key not in attack_data_sources:
            available_domains = [d.replace('-attack', '') for d in attack_data_sources.keys()]
            error_msg = f"Domain '{domain}' not loaded. Available domains: {', '.join(available_domains)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Successfully retrieved attack data for domain: {domain}")
        return attack_data_sources[domain_key]

    except Exception as e:
        logger.error(f"Error getting attack data for domain {domain}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


#####################################################################
# Helper function for formatting MITRE ATT&CK objects
#####################################################################


def format_objects(
    objects: List[Any], include_description: bool = None, domain: str = "enterprise"
) -> str:
    """Format a list of MITRE ATT&CK objects into a readable string

    Args:
        objects: List of objects to format
        include_description: Whether to include description field (default is None, which is system-determined)
        domain: Domain name ('enterprise', 'mobile', or 'ics')

    Returns:
        Formatted string with object information
    """
    formatted_results = []

    # Get the appropriate attack data source
    attack_data = get_attack_data(domain)

    for obj in objects:
        result = ""

        # Handle different input formats (direct object or dict with 'object' key)
        if isinstance(obj, dict) and "object" in obj:
            obj = obj["object"]

        # Add source STIX ID of relationship if available
        if hasattr(obj, "source_ref"):
            attack_id = attack_data.get_object_by_stix_id(obj.source_ref)
            result += f"Source Reference: {obj.source_ref}\n"

        # Build format string based on available attributes
        if hasattr(obj, "name"):
            result += f"Name: {obj.name}\n"

        # Add ID if possible (either directly or via STIX ID)
        if hasattr(obj, "id"):
            attack_id = attack_data.get_attack_id(obj.id)
            result += f"ID: {attack_id}\n"
        else:
            result += f"ID: {obj.id}\n"

        result += f"STIX ID: {obj.id}\n"

        # Add description if available and requested
        if include_description and hasattr(obj, "description"):
            result += f"Description: {obj.description}\n"

        # Add aliases if available
        if hasattr(obj, "aliases"):
            result += f"Aliases: {obj.aliases}\n"

        formatted_results.append(result.strip())

    return "\n---\n".join(formatted_results)


#####################################################################
# Basic object lookup functions
#####################################################################


@mcp.tool()
async def get_object_by_attack_id(
    attack_id: str,
    stix_type: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get object by ATT&CK ID (case-sensitive)

    Args:
        attack_id: ATT&CK ID to find associated object for
        stix_type: TheSTIX object type (must be 'attack-pattern', 'malware', 'tool', 'intrusion-set',
            'campaign', 'course-of-action', 'x-mitre-matrix', 'x-mitre-tactic',
            'x-mitre-data-source', 'x-mitre-data-component', or 'x-mitre-asset')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    logger.info(f"Getting object by ATT&CK ID: {attack_id}, type: {stix_type}, domain: {domain}")
    
    try:
        attack_data = get_attack_data(domain)
        object = attack_data.get_object_by_attack_id(attack_id, stix_type)
        logger.debug(f"Successfully retrieved object for {attack_id}")
        return format_objects(
            [object], include_description=include_description, domain=domain
        )
    except Exception as e:
        logger.error(f"Error getting object by ATT&CK ID {attack_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@mcp.tool()
async def get_object_by_stix_id(
    stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get object by STIX ID (case-sensitive)

    Args:
        stix_id: ATT&CK ID to find associated object for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    object = attack_data.get_object_by_stix_id(stix_id)
    return format_objects(
        [object], include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_objects_by_name(
    name: str,
    stix_type: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get objects by name (case-sensitive)

    Args:
        name: Name of the object to search for
        stix_type: TheSTIX object type (must be 'attack-pattern', 'malware', 'tool', 'intrusion-set',
            'campaign', 'course-of-action', 'x-mitre-matrix', 'x-mitre-tactic',
            'x-mitre-data-source', 'x-mitre-data-component', or 'x-mitre-asset')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    objects = attack_data.get_objects_by_name(name, stix_type)
    return format_objects(
        objects, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_objects_by_content(
    content: str,
    object_type: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get objects by the content of their description

    Args:
        name: Name of the object to search for
        object_type: The STIX object type (must be 'attack-pattern', 'malware', 'tool', 'intrusion-set',
            'campaign', 'course-of-action', 'x-mitre-matrix', 'x-mitre-tactic',
            'x-mitre-data-source', 'x-mitre-data-component', or 'x-mitre-asset')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    objects = attack_data.get_objects_by_content(content, object_type)
    return format_objects(
        objects, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_stix_type(stix_id: str, domain: str = "enterprise") -> str:
    """Get object type by stix ID

    Args:
        stix_id: ATT&CK ID to find associated object type for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
    """
    attack_data = get_attack_data(domain)
    stix_type = attack_data.get_stix_type(stix_id)
    return f"STIX Type: {stix_type}"


@mcp.tool()
async def get_attack_id(stix_id: str, domain: str = "enterprise") -> str:
    """Get attack ID for given stix ID

    Args:
        stix_id: STIX ID to find associated ATT&CK ID for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
    """
    attack_data = get_attack_data(domain)
    attack_id = attack_data.get_attack_id(stix_id)
    return f"ATT&CK ID: {attack_id}"


@mcp.tool()
async def get_name(stix_id: str, domain: str = "enterprise") -> str:
    """Get name for given stix ID

    Args:
        stix_id: STIX ID to find associated name for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
    """
    attack_data = get_attack_data(domain)
    name = attack_data.get_name(stix_id)
    return f"Name: {name}"


#####################################################################
# Threat Actor Group functions
#####################################################################


@mcp.tool()
async def get_groups_by_alias(
    alias: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get MITRE ATT&CK group ID and description by their alias

    Args:
        alias: alias of a MITRE ATT&CK group
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    groups = attack_data.get_groups_by_alias(alias)
    return format_objects(
        groups, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_used_by_group(
    group_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all MITRE ATT&CK techniques used by group by group STIX ID

    Args:
        group_stix_id: Group STIX ID belonging to requested MITRE ATT&CK group
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_used_by_group(group_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_software_used_by_group(
    group_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get software used by MITRE ATT&CK group STIX id

    Args:
        group_stix_id: Group STIX ID belonging to requested MITRE ATT&CK group
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    softwares = attack_data.get_software_used_by_group(group_stix_id)
    return format_objects(
        softwares, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_campaigns_attributed_to_group(
    group_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all campaigns attributed to group by group STIX ID

    Args:
        group_stix_id: Group STIX ID belonging to requested MITRE ATT&CK group
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    campaigns = attack_data.get_campaigns_attributed_to_group(group_stix_id)
    return format_objects(
        campaigns, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_used_by_group_software(
    group_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get techniques used by group's software

    Args:
        group_stix_id: Group STIX ID to check what software they use, and what techniques that software uses
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_used_by_group_software(group_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_groups_using_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get groups using a technique by its STIX ID

    Args:
        technique_stix_id: Technique STIX ID to check what groups are associated with it.
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    groups = attack_data.get_groups_using_technique(technique_stix_id)
    return format_objects(
        groups, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_groups_using_software(
    software_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get groups using software by software name

    Args:
        software_stix_id: Software STIX ID to check which groups use the given software
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    groups = attack_data.get_groups_using_software(software_stix_id)
    return format_objects(
        groups, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_groups_attributing_to_campaign(
    campaign_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get groups attributing to campaign

    Args:
        campaign_stix_id: Campaign STIX ID to look up what groups have been attributed to it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    groups = attack_data.get_groups_attributing_to_campaign(campaign_stix_id)
    return format_objects(
        groups, include_description=include_description, domain=domain
    )


#####################################################################
# Software functions
#####################################################################


@mcp.tool()
async def get_software_by_alias(
    alias: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get software by it's alias

    Args:
        alias: Software name alias to find in MITRE ATT&CK
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    softwares = attack_data.get_software_by_alias(alias)
    return format_objects(
        softwares, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_software_using_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get software using technique

    Args:
        technique_stix_id: Technique STIX ID to search software that uses it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    softwares = attack_data.get_software_using_technique(technique_stix_id)
    return format_objects(
        softwares, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_used_by_software(
    software_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get techniques used by software

    Args:
        software_stix_id: Software STIX ID to check what techniques are associated with it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_used_by_software(software_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


#####################################################################
# "Get All" functions for MITRE ATT&CK objects
#####################################################################


@mcp.tool()
async def get_all_techniques(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all techniques in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques(remove_revoked_deprecated=True)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_subtechniques(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all subtechniques in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    subtechniques = attack_data.get_techniques(
        remove_revoked_deprecated=True, include_subtechniques=True
    )
    # Filter to only include subtechniques (those with a parent)
    subtechniques = [
        t
        for t in subtechniques
        if attack_data.get_parent_technique_of_subtechnique(t.id)
    ]
    return format_objects(
        subtechniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_parent_techniques(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all parent techniques in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques(remove_revoked_deprecated=True)
    # Filter to only include parent techniques (exclude subtechniques)
    parent_techniques = [
        t for t in techniques if not "." in attack_data.get_attack_id(t.id)
    ]
    return format_objects(
        parent_techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_groups(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all threat actor groups in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    groups = attack_data.get_groups()
    return format_objects(
        groups, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_software(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all software in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    software = attack_data.get_software()
    return format_objects(
        software, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_mitigations(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all mitigations in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    mitigations = attack_data.get_mitigations()
    return format_objects(
        mitigations, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_tactics(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all tactics in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    tactics = attack_data.get_tactics()
    return format_objects(
        tactics, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_matrices(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all matrices in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    matrices = attack_data.get_matrices()
    return format_objects(
        matrices, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_campaigns(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all campaigns in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    campaigns = attack_data.get_campaigns()
    return format_objects(
        campaigns, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_datasources(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all data sources in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    datasources = attack_data.get_datasources()
    return format_objects(
        datasources, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_all_datacomponents(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all data components in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    datacomponents = attack_data.get_datacomponents()

    # Special handling for datacomponents which need datasource name
    formatted_results = []

    for datacomponent in datacomponents:
        datasource = attack_data.get_object_by_stix_id(
            datacomponent.x_mitre_data_source_ref
        )

        result = (
            f"Name Data Source: {datasource.name}\n"
            f"Name Data Component: {datacomponent.name}\n"
            f"ID: {attack_data.get_attack_id(datasource.id)}\n"
            f"STIX ID: {datacomponent.id}"
        )

        if include_description and hasattr(datacomponent, "description"):
            result += f"\nDescription: {datacomponent.description}"

        formatted_results.append(result)

    return "\n---\n".join(formatted_results)


@mcp.tool()
async def get_all_assets(domain: str = "ics", include_description: bool = False) -> str:
    """Get all assets in the MITRE ATT&CK framework (ICS domain only)

    Args:
        domain: Domain name ('ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    assets = attack_data.get_assets()
    return format_objects(
        assets, include_description=include_description, domain=domain
    )


#####################################################################
# Campaign functions
#####################################################################


@mcp.tool()
async def get_campaigns_using_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get all campaigns in which a technique is used by its STIX ID

    Args:
        technique_stix_id: Technique STIX ID to look up campaigns in which it is used
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    campaigns = attack_data.get_campaigns_using_technique(technique_stix_id)
    return format_objects(
        campaigns, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_used_by_campaign(
    campaign_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get techniques used by campaign

    Args:
        campaign_stix_id: Campaign STIX ID to check what techniques are used in it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_used_by_campaign(campaign_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_campaigns_using_software(
    software_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all campaigns that use software

    Args:
        software_stix_id: Software STIX ID to look up campaigns in which it is used
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    campaigns = attack_data.get_campaigns_using_software(software_stix_id)
    return format_objects(
        campaigns, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_software_used_by_campaign(
    campaign_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get software used by campaign

    Args:
        campaign_stix_id: Campaign STIX ID to look up what software has been used in it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    softwares = attack_data.get_software_used_by_campaign(campaign_stix_id)
    return format_objects(
        softwares, include_description=include_description, domain=domain
    )


#####################################################################
# Technique functions
#####################################################################


@mcp.tool()
async def get_techniques_by_platform(
    platform: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get techniques by the platform provided (Windows, Linux etc.)

    Args:
        platform: Platform (Windows, Linux etc.) to find associated techniques for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_by_platform(platform)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_parent_technique_of_subtechnique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get parent technique of subtechnique

    Args:
        technique_stix_id: Subtechnique STIX ID to check what its parent technique is
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_parent_technique_of_subtechnique(technique_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_subtechniques_of_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get subtechniques of technique

    Args:
        technique_stix_id: Technique STIX ID to check what its subtechniques are
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_subtechniques_of_technique(technique_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_by_tactic(
    tactic: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all techniques of the given tactic

    Args:
        tactic: Tactic name to lookup techniques for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_by_tactic(
        tactic, f"{domain}-attack", remove_revoked_deprecated=True
    )
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


#####################################################################
# Mitigation functions
#####################################################################


@mcp.tool()
async def get_techniques_mitigated_by_mitigation(
    mitigation_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get techniques mitigated by mitigation

    Args:
        mitigation_stix_id: Mitigation STIX ID to check what techniques are mitigated by it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_mitigated_by_mitigation(mitigation_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_mitigations_mitigating_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get mitigations mitigating technique

    Args:
        technique_stix_id: Technique STIX ID to what mitigations are mitigating this technique
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    mitigations = attack_data.get_mitigations_mitigating_technique(technique_stix_id)
    return format_objects(
        mitigations, include_description=include_description, domain=domain
    )


#####################################################################
# Data component and detection functions
#####################################################################


@mcp.tool()
async def get_datacomponents_detecting_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get datacomponents that detect the given technique

    Args:
        technique_stix_id: Technique STIX ID to check what datacomponents detect it
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    datacomponents = attack_data.get_datacomponents_detecting_technique(
        technique_stix_id
    )

    # Special handling for datacomponents which need datasource name
    formatted_results = []

    for item in datacomponents:
        datacomponent = item["object"]
        datasource = attack_data.get_object_by_stix_id(
            datacomponent.x_mitre_data_source_ref
        )

        result = (
            f"Name Data Source: {datasource.name}\n"
            f"Name Data Component: {datacomponent.name}\n"
            f"ID: {attack_data.get_attack_id(datasource.id)}\n"
            f"STIX ID: {datasource.id}"
        )

        if include_description and hasattr(datacomponent, "description"):
            result += f"\nDescription: {datacomponent.description}"

        formatted_results.append(result)

    return "\n---\n".join(formatted_results)


@mcp.tool()
async def get_techniques_detected_by_datacomponent(
    datacomponent_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get techniques detected by a datacomponent

    Args:
        datacomponent_stix_id: Datacomponent STIX ID to check what techniques it detects
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_detected_by_datacomponent(
        datacomponent_stix_id
    )
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_procedure_examples_by_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get procedure examples by technique STIX ID (shows how groups use a technique)

    Args:
        technique_stix_id: Technique STIX ID to check how they are used and in what procedure
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    procedure_examples = attack_data.get_procedure_examples_by_technique(
        technique_stix_id
    )
    return format_objects(
        procedure_examples, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_assets_targeted_by_technique(
    technique_stix_id: str, domain: str = "ics", include_description: bool = False
) -> str:
    """Get assets targeted by technique STIX ID (shows how assets are targeted by technique), only pertains to ICS domain

    Args:
        technique_stix_id: Technique STIX ID to check what assets are targeted by it
        domain: Domain name ('ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    assets = attack_data.get_assets_targeted_by_technique(technique_stix_id)
    return format_objects(
        assets, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_campaigns_by_alias(
    alias: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get campaigns by their alias

    Args:
        alias: Alias to find associated campaigns for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    campaigns = attack_data.get_campaigns_by_alias(alias)
    return format_objects(
        campaigns, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_objects_by_type(
    stix_type: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get objects by STIX type

    Args:
        stix_type: TheSTIX object type (must be 'attack-pattern', 'malware', 'tool', 'intrusion-set',
            'campaign', 'course-of-action', 'x-mitre-matrix', 'x-mitre-tactic',
            'x-mitre-data-source', 'x-mitre-data-component', or 'x-mitre-asset')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    objects = attack_data.get_objects_by_type(stix_type, remove_revoked_deprecated=True)
    return format_objects(
        objects, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_tactics_by_matrix(
    matrix_stix_id: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get tactics by matrix

    Args:
        matrix_stix_id: Matrix STIX ID to find associated tactics for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    tactics = attack_data.get_tactics_by_matrix(matrix_stix_id)
    return format_objects(
        tactics, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_tactics_by_technique(
    technique_stix_id: str,
    domain: str = "enterprise",
    include_description: bool = False,
) -> str:
    """Get tactics associated with a technique

    Args:
        technique_stix_id: Technique STIX ID to find associated tactics for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    tactics = attack_data.get_tactics_by_technique(technique_stix_id)
    return format_objects(
        tactics, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_procedure_examples_by_tactic(
    tactic: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get procedure examples by tactic (shows how groups use techniques in this tactic)

    Args:
        tactic: Tactic name to check procedure examples for
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    procedure_examples = attack_data.get_procedure_examples_by_tactic(tactic)
    return format_objects(
        procedure_examples, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_techniques_targeting_asset(
    asset_stix_id: str, domain: str = "ics", include_description: bool = False
) -> str:
    """Get techniques targeting a specific asset (ICS domain only)

    Args:
        asset_stix_id: Asset STIX ID to find techniques targeting it
        domain: Domain name ('ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_techniques_targeting_asset(asset_stix_id)
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_objects_created_after(
    timestamp: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get objects created after a specific timestamp

    Args:
        timestamp: ISO format timestamp string (e.g., '2020-01-01T00:00:00Z')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    objects = attack_data.get_objects_created_after(timestamp)
    return format_objects(
        objects, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_objects_modified_after(
    timestamp: str, domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get objects modified after a specific timestamp

    Args:
        timestamp: ISO format timestamp string (e.g., '2020-01-01T00:00:00Z')
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    objects = attack_data.get_objects_modified_after(timestamp)
    return format_objects(
        objects, include_description=include_description, domain=domain
    )


@mcp.tool()
async def get_revoked_techniques(
    domain: str = "enterprise", include_description: bool = False
) -> str:
    """Get all revoked techniques in the MITRE ATT&CK framework

    Args:
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        include_description: Whether to include description in the output (default is False)
    """
    attack_data = get_attack_data(domain)
    techniques = attack_data.get_revoked_techniques()
    return format_objects(
        techniques, include_description=include_description, domain=domain
    )


#####################################################################
# Layer generation functions
#####################################################################


@mcp.tool()
async def generate_layer(attack_id: str, score: int, domain: str = "enterprise", data_path: str = None) -> str:
    """Generate an ATT&CK navigator layer in JSON format based on a matching ATT&CK ID value

    Args:
        attack_id: ATT&CK ID to generate ATT&CK navigator layer for. Valid match values are single ATT&CK ID's for group (GXXX), mitigation (MXXX), software (SXXX), and data component objects (DXXX) within the selected ATT&CK data. NEVER directly input a technique (TXXX). If an invalid match happens, or if multiple ATT&CK ID's are provided, present the user with an error message.
        score: Score to assign to each technique in the layer
        domain: Domain name ('enterprise', 'mobile', or 'ics')
        data_path: Path to the data directory. If None, uses the default cache directory.
    """
    try:
        # Validate input parameters
        valid_domains = ["enterprise", "mobile", "ics"]

        if domain not in valid_domains:
            raise ValueError(
                f"Invalid domain: '{domain}'. Must be one of: {', '.join(valid_domains)}"
            )

        if not attack_id or not isinstance(attack_id, str):
            raise ValueError("match must be a non-empty string")

        # Validate score is an integer
        if not isinstance(score, int):
            raise ValueError("score must be an integer")

        # Validate match format
        if not re.match(r"^[GMSD]\d+$", attack_id):
            raise ValueError(
                "match must be a valid ATT&CK ID format (GXXX, MXXX, SXXX, or DXXX)"
            )

        # Use the provided data path or default
        if data_path is None:
            data_path = get_default_data_dir()

        # Domain key is used in the filename format
        domain_key = f"{domain}-attack"
        stix_path = os.path.join(
            data_path, "v" + release_info.LATEST_VERSION, f"{domain_key}.json"
        )

        # Make sure the STIX file exists
        if not os.path.exists(stix_path):
            raise FileNotFoundError(
                f"STIX data file '{domain_key}.json' not found in data path '{data_path}'. Please ensure the data has been downloaded."
            )

        handle = UsageLayerGenerator(source="local", domain=domain, resource=stix_path)
        layer = handle.generate_layer(match=attack_id)

        if not layer or not layer.layer or not layer.layer.techniques:
            return f"No techniques found for '{attack_id}' in the '{domain}' domain."

        # Filter the techniques where score = 0
        layer.layer.techniques = [t for t in layer.layer.techniques if t.score > 0]

        # Apply score to the techniques
        for t in layer.layer.techniques:
            t.score = score

        return json.dumps(layer.to_dict())

    except ValueError as ve:
        return f"Validation error: {str(ve)}"
    except FileNotFoundError as fe:
        return f"File error: {str(fe)}"
    except KeyError as ke:
        return f"Data error: {str(ke)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


@mcp.tool()
async def get_layer_metadata(domain="enterprise") -> str:
    """
    Always call this tool whenever a prompt requires the generation of a MITRE ATT&CK Navigator Layer,
    such as the generate_layer tool. Always insert this metadata in the generated layer.

    Args:
        domain (str, optional): The ATT&CK domain ('enterprise', 'mobile', or 'ics'). Defaults to 'enterprise'.

    Returns:
        str: JSON string containing the appropriate layer metadata
    """
    # Base metadata template
    base_metadata = {
        "name": "layer",
        "versions": {"attack": "16", "navigator": "5.1.0", "layer": "4.5"},
        "description": "",
        "sorting": 0,
        "layout": {
            "layout": "side",
            "aggregateFunction": "average",
            "expandedSubtechniques": "none",
        },
        "techniques": [],
        "gradient": {
            "colors": ["#ff6666ff", "#ffe766ff", "#8ec843ff"],
            "minValue": 0,
            "maxValue": 100,
        },
        "legendItems": [],
        "metadata": [],
        "links": [],
        "tacticRowBackground": "#dddddd",
    }

    # Domain-specific configurations
    domain_configs = {
        "enterprise": {
            "domain": "enterprise-attack",
            "filters": {
                "platforms": [
                    "Windows",
                    "Linux",
                    "macOS",
                    "Network",
                    "PRE",
                    "Containers",
                    "IaaS",
                    "SaaS",
                    "Office Suite",
                    "Identity Provider",
                ]
            },
        },
        "mobile": {
            "domain": "mobile-attack",
            "filters": {"platforms": ["Android", "iOS"]},
        },
        "ics": {"domain": "ics-attack", "filters": {"platforms": ["None"]}},
    }

    # Validate domain and default to enterprise if invalid
    domain = domain.lower()
    if domain not in domain_configs:
        domain = "enterprise"

    # Add domain-specific configuration to base metadata
    metadata = base_metadata.copy()
    metadata.update(domain_configs[domain])

    return json.dumps(metadata)


def get_cache_dir():
    # `get_cache_dir` identifies the default cache directory for the current user on Windows/Mac/Linux
    # and returns the absolute path to it.
    return get_default_data_dir()


def get_default_data_dir():
    # `get_default_data_dir()` uses a relative directory next to the server to store
    # the mitre-related data. This functionality is used for circumstances where a 
    # data directory hasn't been explictely specified using the command line option `--data-dir`.
    # If the data directory doesn't exist, it will be created by this function.

    # Use a relative directory next to the server
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, DEFAULT_DATA_DIR_NAME)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


#####################################################################
# Prompt Functions for MITRE ATT&CK Analysis
#####################################################################


@mcp.prompt()
def analyze_malware(malware_name: str) -> str:
    """Generate a prompt to analyze malware and find its associated techniques, groups, and campaigns.
    
    Args:
        malware_name: Name or alias of the malware to analyze
    """
    return f"""Analyze the malware '{malware_name}' and provide:
1. What techniques does this malware use?
2. Which threat actor groups are associated with this malware?
3. What campaigns have used this malware?
4. What platforms does this malware target?
5. What mitigations can be applied against this malware?

Use the available MITRE ATT&CK tools to gather comprehensive information about this malware."""


@mcp.prompt()
def compare_ransomware(ransomware1: str, ransomware2: str) -> str:
    """Generate a prompt to compare two ransomware families and find overlapping techniques.
    
    Args:
        ransomware1: Name of the first ransomware family
        ransomware2: Name of the second ransomware family
    """
    return f"""Compare the ransomware families '{ransomware1}' and '{ransomware2}':

1. Find all techniques used by each ransomware family
2. Identify techniques that overlap between both families
3. Highlight unique techniques for each family
4. Generate an ATT&CK Navigator layer showing:
   - Techniques used by {ransomware1} (score: 1)
   - Techniques used by {ransomware2} (score: 3) 
   - Overlapping techniques (score: 5)
5. Provide a downloadable JSON file for the Navigator layer

Use the available tools to gather data and generate the comparison layer."""


@mcp.prompt()
def extract_ttps_from_text(text_content: str) -> str:
    """Generate a prompt to extract TTPs from unstructured text and create an ATT&CK Navigator layer.
    
    Args:
        text_content: Unstructured text containing TTP descriptions
    """
    return f"""Extract MITRE ATT&CK techniques, tactics, and procedures (TTPs) from the following text and generate an ATT&CK Navigator layer:

Text to analyze:
{text_content}

Please:
1. Identify all TTPs mentioned in the text
2. Map them to specific MITRE ATT&CK techniques
3. Generate an ATT&CK Navigator layer with:
   - Each identified technique with score 12345
   - Unique colors per tactic
   - Comments explaining how each technique is used
4. Provide a downloadable JSON file for the Navigator layer

Use the available MITRE ATT&CK tools to verify and map the techniques correctly."""


@mcp.prompt()
def threat_actor_analysis(group_name: str) -> str:
    """Generate a prompt to perform comprehensive threat actor group analysis.
    
    Args:
        group_name: Name or alias of the threat actor group
    """
    return f"""Perform a comprehensive analysis of the threat actor group '{group_name}':

1. **Group Information**: Find the group's aliases, description, and attribution
2. **Techniques Used**: List all techniques employed by this group
3. **Software Used**: Identify all software and tools used by this group
4. **Campaigns**: Find campaigns attributed to this group
5. **Targeting**: What platforms and sectors does this group target?
6. **Timeline**: When was this group first observed?
7. **Mitigations**: What defensive measures can be taken against this group's techniques?

Use the available MITRE ATT&CK tools to gather comprehensive intelligence about this threat actor group."""


@mcp.prompt()
def technique_analysis(technique_id: str) -> str:
    """Generate a prompt to analyze a specific ATT&CK technique in detail.
    
    Args:
        technique_id: ATT&CK technique ID (e.g., T1055, T1059.001)
    """
    return f"""Analyze the MITRE ATT&CK technique '{technique_id}' in detail:

1. **Technique Details**: Get the full description, platforms, and permissions required
2. **Sub-techniques**: If it's a parent technique, list all sub-techniques
3. **Parent Technique**: If it's a sub-technique, identify the parent technique
4. **Tactics**: What tactics does this technique belong to?
5. **Groups Using**: Which threat actor groups use this technique?
6. **Software Using**: What malware and tools use this technique?
7. **Campaigns**: Which campaigns have employed this technique?
8. **Mitigations**: What defensive measures can detect or prevent this technique?
9. **Data Sources**: What data sources can detect this technique?
10. **Procedure Examples**: How do real threat actors use this technique?

Use the available MITRE ATT&CK tools to provide comprehensive analysis of this technique."""


@mcp.prompt()
def campaign_investigation(campaign_name: str) -> str:
    """Generate a prompt to investigate a specific campaign and its TTPs.
    
    Args:
        campaign_name: Name or alias of the campaign to investigate
    """
    return f"""Investigate the campaign '{campaign_name}' and analyze its attack patterns:

1. **Campaign Details**: Get the campaign description, aliases, and attribution
2. **Attributed Groups**: Which threat actor groups are linked to this campaign?
3. **Techniques Used**: What techniques were employed in this campaign?
4. **Software Used**: What malware and tools were used?
5. **Targeting**: What sectors and platforms were targeted?
6. **Timeline**: When did this campaign occur?
7. **Generate Navigator Layer**: Create an ATT&CK Navigator layer showing:
   - All techniques used in this campaign
   - Score each technique based on frequency of use
   - Add comments with real-world usage examples
8. **Defensive Recommendations**: What mitigations should organizations implement?

Use the available MITRE ATT&CK tools to gather intelligence and generate the Navigator layer."""


@mcp.prompt()
def sector_analysis(sector: str) -> str:
    """Generate a prompt to analyze threats targeting a specific sector.
    
    Args:
        sector: Industry sector to analyze (e.g., healthcare, finance, energy)
    """
    return f"""Analyze threats targeting the '{sector}' sector:

1. **Threat Landscape**: What are the main threats to this sector?
2. **Common Techniques**: What techniques are frequently used against this sector?
3. **Threat Actors**: Which groups target this sector?
4. **Campaigns**: What recent campaigns have targeted this sector?
5. **Sector-Specific TTPs**: Are there techniques specific to this sector?
6. **Defensive Strategy**: Generate an ATT&CK Navigator layer with:
   - Techniques commonly used against this sector
   - Prioritized by likelihood and impact
   - Color-coded by threat level
7. **Mitigation Recommendations**: What defensive measures should this sector implement?

Use the available MITRE ATT&CK tools to provide sector-specific threat intelligence."""


@mcp.prompt()
def rainbow_layer() -> str:
    """Generate a prompt to create a colorful rainbow ATT&CK Navigator layer."""
    return """Create a rainbow-colored ATT&CK Navigator layer with all techniques:

1. **Rainbow Colors**: Assign each technique a unique color from the rainbow spectrum
2. **All Techniques**: Include all available techniques from the Enterprise domain
3. **Color Pattern**: Use a systematic color distribution across the rainbow
4. **Visual Appeal**: Make it visually striking and colorful
5. **Downloadable**: Provide a downloadable JSON file for the Navigator

This is for visual demonstration and fun - create the most colorful ATT&CK layer possible!"""


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    print(f"\n🛑 Server shutdown requested (signal {signum})")
    print("👋 Goodbye!")
    shutdown_requested = True
    sys.exit(0)


def run_as_http(host, port):
    """Run the MCP server as an HTTP server using uvicorn"""
    import uvicorn
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    
    try:
        # Create ASGI application
        app = mcp.http_app()
        
        # Run the ASGI application with uvicorn
        # Configure uvicorn to handle signals properly
        config = uvicorn.Config(
            app, 
            host=host, 
            port=port, 
            log_level="info",
            access_log=True,
            # Enable graceful shutdown
            lifespan="on"
        )
        server = uvicorn.Server(config)
        
        # Set up signal handlers for graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down HTTP server...")
            print(f"\n🛑 HTTP server shutdown requested (signal {signum})")
            print("👋 Goodbye!")
            server.should_exit = True
            
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        # Run the server
        server.run()
        
    except KeyboardInterrupt:
        logger.info("HTTP server interrupted by user")
        print("\n🛑 HTTP server shutdown requested by user (Ctrl+C)")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"HTTP server error: {str(e)}")
        raise


def main():
    logger.info("Starting MITRE ATT&CK MCP Server")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--data-dir",
            "-d",
            default=get_default_data_dir(),
            help="Location to store Mitre-related data. Defaults to current users default cache directory.",
        )
        parser.add_argument(
            "--transport",
            "-t",
            choices=["stdio", "http"],
            default="stdio",
            help="Transport protocol to use. Defaults to stdio.",
        )
        parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="Host to bind the server to. Defaults to 0.0.0.0.",
        )
        parser.add_argument(
            "--port",
            "-p",
            type=int,
            default=8032,
            help="Port to bind the server to. Defaults to 8032.",
        )

        args = parser.parse_args()
        
        # Override with environment variables if provided
        if os.getenv("MCP_HOST"):
            args.host = os.getenv("MCP_HOST")
            logger.info(f"Overriding host with MCP_HOST: {args.host}")
        
        if os.getenv("MCP_PORT"):
            args.port = int(os.getenv("MCP_PORT"))
            logger.info(f"Overriding port with MCP_PORT: {args.port}")
        
        if os.getenv("MCP_TRANSPORT"):
            args.transport = os.getenv("MCP_TRANSPORT")
            logger.info(f"Overriding transport with MCP_TRANSPORT: {args.transport}")
        
        if os.getenv("MCP_DATA_DIR"):
            args.data_dir = os.getenv("MCP_DATA_DIR")
            logger.info(f"Overriding data directory with MCP_DATA_DIR: {args.data_dir}")
        logger.info(f"Using data directory: {args.data_dir}")
        logger.info(f"Transport: {args.transport}")
        if args.transport == "http":
            logger.info(f"Host: {args.host}, Port: {args.port}")

        # Check if data files exist in the specified path
        data_exists = all(
            os.path.exists(
                os.path.join(
                    args.data_dir,
                    "v" + release_info.LATEST_VERSION,
                    f"{domain}-attack.json",
                )
            )
            for domain in ["enterprise", "mobile", "ics"]
        )

        logger.debug(f"Data exists check result: {data_exists}")

        # Download data if requested or if files don't exist
        if not data_exists:
            logger.info("Data not found, downloading STIX data")
            download_stix_data(args.data_dir)
        else:
            logger.info("Data already exists, skipping download")

        # Load STIX data from the specified path
        logger.info("Loading STIX data")
        loaded_domains = load_stix_data(args.data_dir)

        if not loaded_domains:
            logger.error("No domains could be loaded, exiting")
            exit(1)

        logger.info(f"Successfully loaded domains: {loaded_domains}")
        
        # Run server with specified transport
        if args.transport == "http":
            logger.info("Starting MCP server with HTTP transport")
            run_as_http(args.host, args.port)
        else:
            logger.info("Starting MCP server with stdio transport")
            try:
                mcp.run(transport="stdio")
            except KeyboardInterrupt:
                logger.info("STDIO server interrupted by user")
                print("\n🛑 STDIO server shutdown requested by user (Ctrl+C)")
                print("👋 Goodbye!")
                sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C), shutting down gracefully...")
        print("\n🛑 Server shutdown requested by user (Ctrl+C)")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
