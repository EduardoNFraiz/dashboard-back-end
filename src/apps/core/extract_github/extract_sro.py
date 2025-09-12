from .extract_base import ExtractBase  # noqa: I001
from typing import Any  # noqa: I001
from py2neo import Node  # noqa: I001
from .logging_config import LoggerFactory  # noqa: I001
import json  # noqa: I001
from apps.core.extract_github.seon_concepts_dictionary import PULLREQUEST, DEVELOPMENTTASK, CREATED_BY, LABEL, MILESTONE, PULLREQUEST, PERSON, COMMIT,SOURCEREPOSITORY, HAS, PRESENT_IN, LABELED, MERGED, MERGED_INTO, COMMITTED_IN, REVIEWED_BY, ASSIGNED_TO, PART_OF # noqa: I001

class ExtractSRO(ExtractBase):
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
            "issues",
            "pull_request_commits",
            "pull_requests",
            "issue_labels",
        ]
        super().__init__(organization=organization, secret=secret, repository=repository,streams=streams)
        self.logger.debug("Initialized Extract SRO with streams: %s", self.streams)

    def fetch_data(self) -> None:
        """Fetch data from Airbyte cache and store in memory as pandas DataFrames."""
        self.logger.info("Fetching data from Airbyte cache...")
        self.load_data()

        if "issues" in self.cache:
            self.issues = self.cache["issues"].to_pandas()
            self.logger.info(f"{len(self.issues)} issues loaded.")

        if "pull_request_commits" in self.cache:
            self.pull_request_commits = self.cache["pull_request_commits"].to_pandas()
            self.logger.info(
                f"{len(self.pull_request_commits)} pull_request_commits loaded."
            )

        if "pull_requests" in self.cache:
            self.pull_requests = self.cache["pull_requests"].to_pandas()
            self.logger.info(f"{len(self.pull_requests)} pull_requests loaded.")

        if "issue_labels" in self.cache:
            self.issue_labels = self.cache["issue_labels"].to_pandas()
            self.logger.info(f"{len(self.issue_labels)} issue_labels loaded.")

  
    def __load_issue(self) -> None:
        """Create Issue nodes and link."""
        self.logger.info("Loading issues...")
        for issue in self.issues.itertuples(index=False):
            data = self.transform(issue)
            self.logger.debug("Issue transformed: %s", data)

            node = self._create_issue_node(data, issue)
            self._link_issue_to_repository(node, issue)
            self._link_issue_to_milestone(node, issue)
            self._link_issue_to_users(node, issue)
            self._link_issue_to_labels(node, issue)
            self._link_issue_to_pull_request(node,issue)
    
    def _link_issue_to_pull_request(self, node: Node, issue: Any) -> None:
        """create a link bettween issue and pullrquest"""
        pullrequest = issue.pull_request
        if pullrequest:
            pull_request_node = self.get_node(PULLREQUEST, url=pullrequest["url"])

            if pull_request_node:

                url = pullrequest["url"]
                self.logger.debug(
                        f"Processing ({url} pull request for issue: {issue.title}"
                    )
                
                self.create_relationship(pull_request_node, HAS, node)
               # self.create_relationship(node, PART_OF, pull_request_node)
                self.logger.info(
                        f"Linked Issue to Pull Request: {issue.title} - {url}"
                    )
            else:
                ## TODO .. fazer uma chamada de API para buscar o pull request
                pullrequest["id"] =  pullrequest["url"]
                pullrequest["problem"] =  True
                pull_request_node = self.create_node(pullrequest, PULLREQUEST, "id")
                self.logger.warning(f"Pull Request not found for issue: {issue.title}")

        
    def _create_issue_node(self, data: dict[str, Any], issue: Any) -> Node:
        """Create the Issue node in Neo4j."""
        self.logger.debug("Creating Issue node...")
        node = self.create_node(data, DEVELOPMENTTASK, "id")
        self.logger.info(f"Issue node created: {issue.title}")
        return node

    def _link_issue_to_repository(self, node: Node, issue: Any) -> None:
        """Link the Issue node to its repository."""
        repository_node = self.get_node(SOURCEREPOSITORY, full_name=issue.repository)
        if repository_node:
            self.create_relationship(repository_node, HAS, node)
            self.logger.info(
                f"Linked Repository to Issue: {issue.title} - {issue.repository}"
            )
        else:
            self.logger.warning(f"Repository not found for issue: {issue.title}")

    def _link_issue_to_milestone(self, node: Node, issue: Any) -> None:
        """Link the Issue to its Milestone, if any."""
        if issue.milestone:
            self.logger.debug(f"Linking Issue to Milestone: {issue.title}")
            milestone = issue.milestone
            milestone_id = milestone["id"]
            milestone_node = self.get_node(MILESTONE, id=milestone_id)
            if milestone_node:
                self.create_relationship(milestone_node, HAS, node)
                self.logger.info(
                    f"Linked Milestone to Issue: {issue.title} - {milestone_id}"
                )
            else:
                self.logger.warning(f"Milestone not found for issue: {issue.title}")

    def _link_issue_to_users(self, node: Node, issue: Any) -> None:
        """Link the Issue to its creator and assignees."""
        if issue.user:
            self._create_user_relationship(node, issue.user, CREATED_BY, issue.title)

        if issue.assignee:
            self._create_user_relationship(
                node, issue.assignee, ASSIGNED_TO, issue.title
            )

        if issue.assignees:
            assignees = issue.assignees
            self.logger.debug(
                f"Processing {len(assignees)} assignees for issue: {issue.title}"
            )
            for assignee in assignees:
                self._create_user_relationship(
                    node, assignee, ASSIGNED_TO, issue.title
                )
         

    def _create_user_relationship(
        self, node: Node, user_data: Any, rel_type: str, issue_title: str
    ) -> None:
        """Create a relationship between the Issue and a user (creator or assignee)."""
        user = (
            user_data
            if isinstance(user_data, dict)
            else self.transform_object(user_data)
        )
        login = user.get("login") if isinstance(user, dict) else user.login
        user_node = self.get_node(PERSON, id=login)
        if user_node:
            self.create_relationship(node, rel_type, user_node)
            self.logger.info(
                f"Linked {rel_type} between Issue and User: {login} - {issue_title}"
            )
        else:
            self.logger.warning(
                f"User node not found: {login} for {rel_type} on {issue_title}"
            )
            login = user["login"]
            user["id"] = login
            user["name"] = login

            user_node = self.create_node(user, PERSON, "id")
            self.create_relationship(user_node, PRESENT_IN, self.organization_node)
            self.create_relationship(node, rel_type, user_node)
          
            self.logger.info(
                f"Linked {rel_type} between Issue and User: {login} - {issue_title}"
            )


    def _link_issue_to_labels(self, node: Node, issue: Any) -> None:
        """Link the Issue to its associated Labels."""
        if issue.labels:
            labels = issue.labels
            self.logger.debug(
                f"Processing {len(labels)} labels for issue: {issue.title}"
            )
            for label in labels:
                label_node = self.get_node(LABEL, id=label["id"])
                if label_node:
                    self.create_relationship(node, LABELED, label_node)
                    self.logger.info(
                        f"Labeled issue {issue.title} with {label['name']}"
                    )
                else:
                    self.logger.warning(
                        f"Label not found: {label['id']} for issue {issue.title}"
                    )

    def __load_pull_request_commit(self) -> None:
        """Link commits to their respective Pull Requests."""
        self.logger.info("Linking commits to pull requests...")
        for pr_commit in self.pull_request_commits.itertuples(index=False):
            data = self.transform(pr_commit)
            commit_node = self.get_node(COMMIT, sha=data["sha"])
            pr_node = self.get_node(
                PULLREQUEST, repository=data["repository"], number=data["pull_number"]
            )
            if commit_node and pr_node:
                self.create_relationship(commit_node, COMMITTED_IN, pr_node)
               # self.create_relationship(pr_node, HAS, commit_node)
                self.logger.info("Linked commit to pull_request")
            else:
                self.logger.warning(
                    "Commit or PullRequest not found for commit SHA: %s", data["sha"]
                )

    def __load_pull_requests(self) -> None:
        """Create Pull Request nodes and link."""
        self.logger.info("Loading pull requests...")
        for pr in self.pull_requests.itertuples(index=False):
            data = self.transform(pr)
            node = self.create_node(data, PULLREQUEST, "id")
            self.logger.debug(f"Created PullRequest node: {pr.title}")

            repository_node = self.get_node(SOURCEREPOSITORY, full_name=pr.repository)
            if repository_node:
                self.create_relationship(repository_node, HAS, node)

            if pr.labels:
                labels = pr.labels
                for label in labels:
                    label_node = self.get_node(LABEL, id=label["id"])
                    if label_node:
                        self.create_relationship(node, LABELED, label_node)

            if pr.milestone:
                milestone = pr.milestone
                milestone_node = self.get_node(MILESTONE, id=milestone["id"])
                if milestone_node:
                    self.create_relationship(node, HAS, milestone_node)

            if pr.merge_commit_sha:
                commit_node = self.get_node(COMMIT, sha=pr.merge_commit_sha)
                if commit_node:
                    self.create_relationship(node, MERGED, commit_node)
                    #self.create_relationship(commit_node, MERGED_INTO, node)

            self.logger.info(f"Linking users to pull request: {pr.title}")
            self._link_issue_to_users(node, pr)
            
            if pr.requested_reviewers:
                reviewers = pr.requested_reviewers
                self.logger.debug(
                    f"Procssing {len(reviewers)} reviewers for pull: {pr.title}"
                )
                for reviewer in reviewers:
                    login = reviewer.get("login")
                    user_node = self.get_node(PERSON, id=login)
                    if user_node:
                        self.create_relationship(
                                node, REVIEWED_BY, user_node)
                        self.logger.info(
                            f"Pull Request {node} reviewed by : {user_node}"
                        )
                    else:
                        login = reviewer["login"]
                        reviewer["id"] = login
                        reviewer["name"] = login

                        user_node = self.create_node(reviewer, PERSON, "id")
                        self.create_relationship(user_node, PRESENT_IN, self.organization_node)
                        self.create_relationship(node, REVIEWED_BY, user_node)

                        self.logger.info(
                            f"Linked present_in between Pull Request and Reviewe: {login} - {node}"
                        )   
    


    def run(self) -> None:
        """Run the full extraction and persistence process."""
        self.logger.info("🔄 Starting SRO extraction pipeline...")
        self.fetch_data()
        self.__load_pull_requests()
        self.__load_pull_request_commit()
        self.__load_issue()
        self.create_config_domain("sro")
        self.logger.info("✅ Extraction completed successfully!")
