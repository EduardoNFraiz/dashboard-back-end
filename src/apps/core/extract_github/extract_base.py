import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import airbyte as ab
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from py2neo import Node, Relationship

from .sink_neo4j import SinkNeo4j
from .logging_config import LoggerFactory
from airbyte.caches import PostgresCache

logger = LoggerFactory.get_logger("extractor")


class ExtractBase(ABC):
    """Base class for data extraction."""

    # Class attributes
    config_node: Any = None  # Config node
    organization_node: Any = None  # Neo4j Node object representing the organization
    token: str = ""  # API token (e.g., GitHub token)
    client: Any = None  # API client (to be defined in subclasses)
    streams: list[str] = []  # List of Airbyte streams to extract
    cache: Any = None  # Local cache managed by Airbyte (DuckDB)
    source: Any = None  # Data source connector (Airbyte)
    sink: Any = None  # Data sink, in this case Neo4j (via SinkNeo4j)
    start_date: datetime = None  # Start date for data extraction

    organization:str = None #Organization
    repository:str = None #epository

    def __init__(self, organization:str, secret:str, repository:str, streams:list[str], start_date:datetime=None) -> None:
        """Post-initialization hook."""
        logger.info("Initializing ExtractBase...")
        load_dotenv()
        logger.debug("Environment variables loaded.")
        
        self.organization = organization
        self.token = secret
        self.repository = repository
        self.streams = streams
        token_len = len(self.token)
        self.start_date = start_date

        logger.info(f"ExtractBase initialized with organization={self.organization}, repository={self.repository}, streams={self.streams}, token_length={token_len}")

        # Initialize the sink (Neo4j by default, but can be overridden)
        try:
            self.sink = self.initialize_sink()
            if self.sink:
                logger.info(f"{self.sink.__class__.__name__} initialized successfully.")
        except Exception as e:
            logger.warning(f"Default sink initialization failed: {e}. Subclasses may provide their own sink.")
            self.sink = None

        # Load GitHub token from .env
        if not self.token:
            logger.warning("GITHUB_TOKEN not found in environment variables.")
        else:
            logger.debug("GitHub token loaded.")

        # If streams are configured, set up the Airbyte source
        if self.streams:
            logger.info(f"Configuring Airbyte source for streams: {self.streams}")
            if not self.repository:
                logger.warning("REPOSITORIES environment variable is not set.")

            config = {
                "repositories": [f"{self.repository}"],
                "credentials": {
                    "personal_access_token": f"{self.token}",
                },
            }
            logger.debug(f"Airbyte source initial config: {config}")

        # Load retrieve date configuration if possible
        if self.sink:
            organization_id = self.organization
            self.config_node = self.get_config(organization_id)

            if self.start_date is None and self.config_node is not None:
                # Handle both dict-like (Neo4j) and object-like (Django) configs
                if hasattr(self.config_node, 'get'):
                    self.start_date = self.config_node.get("last_retrieve_date")
                else:
                    self.start_date = getattr(self.config_node, "last_retrieve_date", None)
                
                if self.start_date:
                    config["start_date"] = self.start_date
                    logger.info(f"Using start_date from config: {config['start_date']}")

        try:
            self.source = ab.get_source(
                "source-github",
                install_if_missing=True,                   
                config=config,
            )
            logger.info("Airbyte source-github obtained.")

            # Check if source credentials and config are valid
            self.source.check()
            logger.info("Airbyte source check passed successfully.")
        except Exception as e:
            logger.error(f"Failed to configure or check Airbyte source: {e}")
            raise

        # Load the organization node if sink is present
        if self.sink and hasattr(self.sink, 'save_node'):
            self.__load_organization()
        
        logger.info("ExtractBase initialization complete.")

    def initialize_sink(self) -> Any:
        """Initialize the default sink. Overridden by subclasses if needed."""
        try:
            return SinkNeo4j()
        except Exception:
            return None

    def get_config(self, organization_id: str) -> Any:
        """Retrieve configuration for this extractor. Overridden by subclasses."""
        if self.sink and hasattr(self.sink, 'get_node'):
            return self.sink.get_node(f"Config_{self.__class__.__name__}", id=organization_id)
        return None

    def load_data(self) -> None:
        """Load data from the Airbyte source into the local cache."""
        if not self.source:
            logger.warning("Airbyte source not initialized. Cannot load data.")
            return

        logger.info(f"Selecting streams to load: {self.streams}")
        self.source.select_streams(self.streams)  # Select streams to load

        logger.info("Initializing Postgres Cache.")
        self.cache = PostgresCache(
            
            host=os.getenv("DB_HOST_LOCAL", "localhost"),
            port=os.getenv("DB_PORT_LOCAL", "localhost"),
            username=os.getenv("DB_USER_LOCAL", "localhost"),
            password=os.getenv("DB_PASSWORD_LOCAL", "localhost"),
            database=os.getenv("DB_NAME_LOCAL", "localhost")
            
        )
        
        logger.info("Reading data from Airbyte source into cache...")
        try:
            self.source.read(cache=self.cache)  # Read data into cache
            logger.info("Data loaded successfully into cache.")
        except Exception as e:
            logger.error(f"Failed to load data from Airbyte source: {e}")
            raise

    def flatten_nested_dict(self, d: dict, parent_key='', sep='.') -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_nested_dict(v, new_key + sep, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)        

    def data_clean (self, data: Any) -> Any:
        clean = {}
        for k, v in data.items():
            if isinstance(v, dict):
                flattened = self.flatten_nested_dict(v, parent_key=k)
                for fk, fv in flattened.items():
                    if isinstance(fv, (str, int, float, bool)) or fv is None:
                        clean[fk] = fv
                    else:
                        clean[fk] = str(fv)
            elif isinstance(v, (str, int, float, bool)) or v is None:
                clean[k] = v
            else:
                clean[k] = str(v)
        return clean


    def safe_nan_to_none(self, v):
        try:
            if isinstance(v, (list, np.ndarray, pd.Series)):
                return [None if pd.isna(item) else item for item in v]
            return None if pd.isna(v) else v
        except TypeError:
            return v


    def transform(self, value: Any) -> Any:
        """Transform a record from Airbyte into a clean dictionary.

        Removes auxiliary fields (starting with "_airbyte")
        and converts NaN values to None.

        Args:
        ----
            value (Any): A single record object.

        Returns:
        -------
            dict: A clean dictionary representation of the record.

        """
        logger.debug(f"Transforming record: {value}")
        data = {
            k: self.safe_nan_to_none(v)
            for k, v in value._asdict().items()  # Convert to dict
            if not k.startswith("_airbyte")  # Remove metadata fields
        }

        clean = self.data_clean(data)
        logger.debug(f"Transformed record: {clean}")
        
        return clean



    def save_node(self, node: Node, type: str, key: str) -> Node:
        """Persist a node into Neo4j.

        Args:
        ----
            node (Node): Py2neo Node object.
            type (str): Node label (e.g., "User", "Repository").
            key (str): Unique property key to identify the node.

        Returns:
        -------
            Node: The persisted node.

        """
        logger.info(
            f"Save node of type '{type}' with key '{key}' and properties: {dict(node)}"
        )
        try:
            persisted_node = self.sink.save_node(node, type, key)
            logger.info(f"Node '{type}' with key '{key}' saved successfully.")
            return persisted_node
        except Exception as e:
            logger.error(f"Failed to save node '{type}' with key '{key}': {e}")
            raise

    def save_relationship(self, element: Relationship) -> Relationship:
        """Persist a relationship into Neo4j.

        Args:
        ----
            element (Relationship): Py2neo Relationship object.

        Returns:
        -------
            Relationship: The persisted relationship.

        """
        logger.info(f"Attempting to save relationship: {element}")
        try:
            persisted_relationship = self.sink.save_relationship(element)
            logger.info(f"Relationship '{element}' saved successfully.")
            return persisted_relationship
        except Exception as e:
            logger.error(f"Failed to save relationship '{element}': {e}")
            raise

    def get_node(self, type_element: str, **properties: Any) -> Node:
        """Retrieve a node from Neo4j based on type and properties.

        Args:
        ----
            type_element (str): Node label (e.g., "User", "Repository").
            **properties (Any): Property filters (e.g., id="123").

        Returns:
        -------
            Node: The matched node, or None if not found.

        """
        logger.info(
            f"Retrieve node of type '{type_element}' with properties: {properties}"
        )
        try:
            node = self.sink.get_node(type_element, **properties)
            if node:
                logger.info(
                    f"Node '{type_element}' with properties {properties} found."
                )
            else:
                logger.info(
                    f"Node '{type_element}' with properties {properties} not found."
                )
            return node
        except Exception as e:
            logger.error(
                f"Failed to retrieve node '{type_element}'"
                + f" with properties {properties}: {e}"
            )
            raise

    @abstractmethod
    def fetch_data(self) -> None:
        """Retrieve data from a data repository."""
        logger.info("Abstract method 'fetch_data' called.")
        pass

    def transform_object(self, value: Any) -> Any:
        """Transform dictionary to object.

        Args:
        ----
            value (Any): dictionary

        Returns:
        -------
            Object: Object

        """
        logger.debug(f"Transforming dictionary to object: {value}")
        try:
            obj = json.loads(value, object_hook=lambda d: SimpleNamespace(**d))
            logger.debug("Dictionary transformed to object successfully.")
            return obj
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error during object transformation: {e}")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during object transformation: {e}"
            )
            raise

    def create_relationship(
        self, node_from: Node, relation: str, node_to: Node
    ) -> None:
        """Create a Relationship between nodes.

        Args:
        ----
            node_from (Node): node source relationship
            relation (str): relation name
            node_to (Node): node target from relationship

        """
        logger.info(
            f"Create relationship '{relation}' "
            f"from {dict(node_from)} "
            f"to {dict(node_to)}"
        )

        try:
            self.sink.save_relationship(Relationship(node_from, relation, node_to))
            logger.info(f"Relationship '{relation}' created successfully.")
        except Exception as e:
            logger.error(f"Failed to create relationship '{relation}': {e}")
            raise

    def create_node(self, data: Any, node_type: str, id_field: str) -> Node:
        """Create a Node.

        Args:
        ----
            data (Any): data to be save in a node
            node_type (str): type of node
            id_field (str): define field that will be node's id

        Returns:
        -------
            Node: a node in a graph

        """
        logger.info(f"Create node '{node_type}' with field '{id_field}': {data}")
        data["created_node_at"] = datetime.now().isoformat()
        node = Node(node_type, **data)
        try:
            self.sink.save_node(node, node_type.strip().lower(), id_field)
            logger.info(
                f"Node '{node_type}' - '{data.get(id_field)}' created and saved."
            )
            return node
        except Exception as e:
            logger.error(
                f"Failed to create and save '{node_type}' '{data.get(id_field)}': {e}"
            )
            raise

    def create_config_domain(self,name:str) -> None:
        """Load retrieve date."""
        logger.info("Creating retrieve date configuration node.")
        
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        # Remove timezone info para formatar como string ISO sem fuso
        start_date = today.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S") + 'Z'


        organization_id = self.organization
        organization_name = self.organization

        if not organization_id:
            logger.warning("ORGANIZATION_ID not found for creating retrieve config.")
            return
        if not organization_name:
            logger.warning("ORGANIZATION not found for creating retrieve config.")
            return

        self.config_node = Node(
            f"Config_{self.__class__.__name__}",
            id=organization_id,
            name=organization_name,
            last_retrieve_date=start_date,
        )
        try:
            self.sink.save_node(self.config_node, "Config", "id")
            logger.info(
                f"Config node created/updated with last_retrieve_date: {start_date}"
            )
        except Exception as e:
            logger.error(f"Failed to save Config node for retrieve date: {e}")
            raise

    def __load_organization(self) -> None:
        """Load the organization node."""
        organization_id = self.organization
        organization_name = self.organization

        if not organization_id:
            logger.warning("ORGANIZATION_ID not found for loading organization node.")
            return
        if not organization_name:
            logger.warning("ORGANIZATION not found for loading organization node.")
            return

        logger.info(f"Attempting to load organization node with ID: {organization_id}")
        self.organization_node = self.sink.get_node("Organization", id=organization_id)
        # If the node does not exist, create it
        if self.organization_node is None:
            logger.info(f"Organization '{organization_id}' not found.")
            self.organization_node = Node(
                "Organization",
                id=organization_id,
                name=organization_name,
            )
            try:
                self.sink.save_node(self.organization_node, "Organization", "id")
                logger.info(
                    f"Organization node '{organization_name}' created and saved."
                )
            except Exception as e:
                logger.error(f"Failed to create and save organization node: {e}")
                raise
        else:
            logger.info(f"Organization '{organization_name}' loaded.")
