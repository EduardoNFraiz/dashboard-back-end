"""Django-based EO (Enterprise Ontology) data extractor.

This module extracts teams, projects, and team members from GitHub
and persists them into Django relational models instead of Neo4j.
"""

import datetime
from typing import Any, List, Dict
from django.utils import timezone as django_timezone
from .extract_base import ExtractBase
from .logging_config import LoggerFactory
from .sink_django import SinkDjango


class ExtractEODjango(ExtractBase):
    """Extracts and loads data related to teams, team members, and projects into Django models."""

    team_members: Any = None
    teams: Any = None
    projects: Any = None
    users: Any = None

    def initialize_sink(self) -> SinkDjango:
        """Initialize the Django sink."""
        return SinkDjango()

    def __init__(self, organization: str, secret: str, repository: str) -> None:
        """Initialize the Django-based EO extractor."""
        self.logger = LoggerFactory.get_logger(__name__)
        streams = ["projects_v2", "teams", "team_members"]
        
        # Call parent init which will now use initialize_sink()
        super().__init__(
            organization=organization,
            secret=secret,
            repository=repository,
            streams=streams,
            start_date=None
        )

    def fetch_data(self) -> None:
        """Load data from the Airbyte cache into pandas DataFrames."""
        self.logger.info("Fetching data from Airbyte cache.")
        try:
            self.load_data()
        except Exception as e:
            self.logger.error(f"Critical error during load_data: {e}")
            return

        if "teams" in self.cache:
            try:
                self.teams = self.cache["teams"].to_pandas()
                self.logger.info("✅ %d teams loaded.", len(self.teams))
            except Exception as e:
                self.logger.warning(f"Could not load 'teams' stream: {e}. This might be due to missing permissions.")

        if "projects_v2" in self.cache:
            try:
                self.projects = self.cache["projects_v2"].to_pandas()
                self.logger.info("✅ %d projects_v2 loaded.", len(self.projects))
            except Exception as e:
                self.logger.warning(f"Could not load 'projects_v2' stream: {e}.")

        if "team_members" in self.cache:
            try:
                self.team_members = self.cache["team_members"].to_pandas()
                self.logger.info("✅ %d team_members loaded.", len(self.team_members))
            except Exception as e:
                self.logger.warning(f"Could not load 'team_members' stream: {e}.")

    def __prepare_teams_data(self) -> List[Dict[str, Any]]:
        """Transform teams DataFrame into list of dictionaries.
        
        Returns:
            List of team data dictionaries
        """
        teams_list = []
        if self.teams is not None:
            for team in self.teams.itertuples():
                data = self.transform(team)
                teams_list.append(data)
                self.logger.info("🔄 Preparing Team... %s", data.get('name', 'Unknown'))
        return teams_list

    def __prepare_projects_data(self) -> List[Dict[str, Any]]:
        """Transform projects DataFrame into list of dictionaries.
        
        Returns:
            List of project data dictionaries
        """
        projects_list = []
        if self.projects is not None:
            for project in self.projects.itertuples():
                data = self.transform(project)
                projects_list.append(data)
                self.logger.info("🔄 Preparing Project... %s", data.get('title', 'Unknown'))
        return projects_list

    def __prepare_team_members_data(self) -> List[Dict[str, Any]]:
        """Transform team members DataFrame into list of dictionaries.
        
        Returns:
            List of team member data dictionaries
        """
        members_list = []
        if self.team_members is not None:
            for member in self.team_members.itertuples():
                data = self.transform(member)
                # Ensure we have login
                if not data.get('login'):
                    data['login'] = member.login if hasattr(member, 'login') else 'unknown'
                
                # Add team_slug if available
                if hasattr(member, 'team_slug'):
                    data['team_slug'] = member.team_slug
                
                members_list.append(data)
                self.logger.info("🔄 Preparing Team Member... %s", data.get('login', 'Unknown'))
        return members_list

    def __save_to_django(self) -> Dict[str, int]:
        """Save all prepared data to Django models.
        
        Returns:
            Dictionary with statistics of saved entities
        """
        self.logger.info("Saving data to Django models...")
        
        # Prepare all data
        teams_data = self.__prepare_teams_data()
        projects_data = self.__prepare_projects_data()
        members_data = self.__prepare_team_members_data()
        
        # Save everything in a transaction
        stats = self.sink.save_extraction_data(
            organization_name=self.organization,
            teams_data=teams_data,
            projects_data=projects_data,
            team_members_data=members_data
        )
        
        self.logger.info("✅ Data saved successfully!")
        self.logger.info("📊 Statistics: %s", stats)
        
        return stats

    def get_config(self, organization_id: str) -> Any:
        """Override to use Django's Configuration model."""
        if self.sink:
            org = self.sink.get_or_create_organization(self.organization)
            config = self.sink.get_configuration(org, self.repository)
            if config:
                # Map Django's start_date to the name expected by ExtractBase
                return {"last_retrieve_date": config.start_date}
        return None

    def create_config_domain(self, name: str) -> None:
        """Override to save configuration in Django."""
        self.logger.info("Saving retrieval date in Django Configuration.")
        if self.sink:
            org = self.sink.get_or_create_organization(self.organization)
            now = django_timezone.now()
            self.sink.save_configuration(org, self.repository, now)

    def run(self) -> Dict[str, Any]:
        """Orchestrate the full extraction and loading process.
        
        Returns:
            Dictionary with execution status and statistics
        """
        self.logger.info("🔄 Starting Django-based extraction for Teams, Projects, and Members...")
        
        try:
            # Fetch data from GitHub via Airbyte
            self.fetch_data()
            
            # Save to Django models
            stats = self.__save_to_django()
            
            # Create config for incremental updates
            self.create_config_domain("eo")
            
            self.logger.info("✅ Extraction completed successfully!")
            
            return {
                "status": "success",
                "statistics": stats,
                "message": "Data extracted and saved to Django models"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
