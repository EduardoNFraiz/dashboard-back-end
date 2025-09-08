from .extract_base import ExtractBase  # noqa: I001
from typing import Any  # noqa: I001
from py2neo import Node  # noqa: I001
from .logging_config import LoggerFactory  # noqa: I001
import json  # noqa: I001
from apps.core.extract_github.seon_concepts_dictionary import CREATED_BY, LABEL, MILESTONE, ISSUE, PULLREQUEST, PERSON, COMMIT,SOURCEREPOSITORY, HAS, PRESENT_IN, LABELED, MERGED, MERGED_INTO, COMMITTED_IN, REVIEWED_BY, ASSIGNED_TO, RELATED_TO, PART_OF # noqa: I001

class ExtractSMPO(ExtractBase):
    """Extract and persist data for the SRO dataset using Airbyte and Neo4j."""

    milestones: Any = None
    issues: Any = None
    pull_request_commits: Any = None
    pull_requests: Any = None
    issue_labels: Any = None
    projects: Any = None

    def __init__(self, organization:str, secret:str, repository:str) -> None:
        """Initialize the extractor and define streams to load from Airbyte."""
        self.logger = LoggerFactory.get_logger(__name__)
        streams = [
            "issue_milestones",
        ]
        super().__init__(organization=organization, secret=secret, repository=repository,streams=streams)
        self.logger.debug("Initialized ExtractSMPO with streams: %s", self.streams)

    def fetch_data(self) -> None:
        """Fetch data from Airbyte cache and store in memory as pandas DataFrames."""
        self.logger.info("Fetching data from Airbyte cache...")
        self.load_data()

        if "issue_milestones" in self.cache:
            self.milestones = self.cache["issue_milestones"].to_pandas()
            self.logger.info(f"{len(self.milestones)} issue_milestones loaded.")

    def __load_milestones(self) -> None:
        """Create Milestone nodes and link them to their respective repositories."""
        self.logger.info("Loading milestones...")
        for milestone in self.milestones.itertuples(index=False):
            data = self.transform(milestone)
            self.logger.debug("Milestone transformed: %s", data)

            milestone_node = self.create_node(data, MILESTONE, "id")
            self.logger.debug("Milestone node created: %s", milestone_node)

            repository_node = self.get_node(
                SOURCEREPOSITORY, full_name=milestone.repository
            )
            if repository_node:
                self.create_relationship(repository_node, HAS, milestone_node)
                self.logger.info(
                    "Linked Repository to Milestone: %s - %s",
                    milestone.repository,
                    milestone.title,
                )
            else:
                self.logger.warning(
                    f"Repository not found for milestone: {milestone.title}"
                )

   

    def run(self) -> None:
        """Run the full extraction and persistence process."""
        self.logger.info("🔄 Starting SMPO extraction pipeline...")
        self.fetch_data()
        self.__load_milestones()
        self.create_config_domain("smpo")
        self.logger.info("✅ Extraction completed successfully!")
        return "done"
