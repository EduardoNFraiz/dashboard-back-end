import datetime
from typing import Any  # noqa: I001
from .extract_base import ExtractBase  # noqa: I001
from .logging_config import LoggerFactory  # noqa: I001
import json  # noqa: I001
from apps.core.extract_github.seon_concepts_dictionary import SOURCEREPOSITORY, PROJECT, PERSON, BRANCH, COMMIT, HAS, PRESENT_IN, CREATED_BY, COMMITTED_BY, IN, IS_PARENT, HAS_PARENT
from github import Github, Repository, Commit as GitCommit  # noqa: I001
from celery import shared_task
from py2neo import Graph  # noqa: I001
import os  # noqa: I001

@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def process_commit(sha: str, repository: str, secret: str) -> None:
    """Fetch files of a given commit from GitHub and create artifacts in Neo4j."""
    try:
        
        logger = LoggerFactory.get_logger(__name__)
        github = Github(secret)
        repo: Repository.Repository = github.get_repo(repository)
        commit_git: GitCommit.Commit = repo.get_commit(sha)
        commit_id = f"{sha}-{repository}"

        sink = Graph(
            "bolt://neo4j:7687",
            auth=(os.getenv("NEO4J_USERNAME", ""), os.getenv("NEO4J_PASSWORD", "")),
        )

        commit_node = sink.get_node("Commit", id=commit_id)
        if not commit_node:
            logger.warning(f"❌ Commit not found in Neo4j: {commit_id}")
            return

        for file in commit_git.files:
            if file.sha:
                data = {
                    "id": file.sha,
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": getattr(file, "patch", None),
                    "raw_url": file.raw_url,
                    "blob_url": file.blob_url,
                    "sha": file.sha,
                }

                file_node = sink.create_node(data, "softwareartifact", "id")
                sink.create_relationship(commit_node, "has", file_node)
                sink.create_relationship(file_node, "commited", commit_node)

                logger.info(f"✅ Processed: file {file.sha} | {sha}")

        logger.info(f"✅ Processed: Commit {sha} | {repository}")

    except Exception as e:
        logger.error(f"⚠️ Error processing {sha} | {repository}: {e}")




class ExtractCMPO(ExtractBase):
    """Extracts CMPO data and stores it in Neo4j."""

    branches: Any = None
    issues: Any = None
    commits: Any = None
    repositories: Any = None
    projects: Any = None
    secret: str = None

    def __init__(self, organization:str, secret:str, repository:str, start_date:datetime=None) -> None:
        """Initialize the extractor and define streams to load from Airbyte."""
        self.logger = LoggerFactory.get_logger(__name__)
        streams = ["repositories", "projects_v2", "commits", "branches"]
        super().__init__(organization=organization, secret=secret, repository=repository,streams=streams, start_date=start_date)            
        self.logger.debug("CMPO extractor initialized with streams: %s", self.streams)
        self.secret = secret

    def fetch_data(self) -> None:
        """Fetch data."""
        self.logger.info("Fetching CMPO data streams...")
        self.load_data()

        if "repositories" in self.cache:
            self.repositories = self.cache["repositories"].to_pandas()
            self.logger.info(f"{len(self.repositories)} repositories loaded.")

        if "projects_v2" in self.cache:
            self.projects = self.cache["projects_v2"].to_pandas()
            self.logger.info(f"{len(self.projects)} projects loaded.")

        if "commits" in self.cache:
            self.commits = self.cache["commits"].to_pandas()
            self.logger.info(f"{len(self.commits)} commits loaded.")

        if "branches" in self.cache:
            self.branches = self.cache["branches"].to_pandas()
            self.logger.info(f"{len(self.branches)} branches loaded.")

    def __load_source_code(self) -> None:
        """Load Source Code."""
        self.logger.info("Loading Source Code...")
        for repository in self.repositories.itertuples():
            data = self.transform(repository)
            self.logger.debug("Source Code transformed: %s", data)
            node = self.create_node(data, SOURCEREPOSITORY, "id")
            self.create_relationship(self.organization_node, HAS, node)
            self.logger.info(f"Source Code node created and linked: {data['id']}")

    def __load_repository_project(self) -> None:
        """Link repositories to projects. or Source Repositories to Projects."""
        self.logger.info("Linking repositories to projects...")
        for project in self.projects.itertuples():
            self.logger.debug("Processing project: %s", project.id)
            repository_node = self.get_node(SOURCEREPOSITORY, full_name=project.repository)
            project_node = self.get_node(PROJECT, id=project.id)

            if repository_node and project_node:
                self.create_relationship(project_node, HAS, repository_node)
                self.logger.info(
                    "Linked Project: %s - %s",
                    project.id,
                    project.repository,
                )
            else:
                self.logger.info(
                    "Missing node for Project %s or Repository %s",
                    project.id,
                    project.repository,
                )

    def flatten_dict(self, d: Any, prefix: Any) -> Any:
        """Flatten a nested dictionary, prefixing keys with their parent path."""
        flat = {}
        for k, v in d.items():
            if isinstance(v, dict):
                flat.update(self.flatten_dict(v, prefix + k + "_"))
            else:
                flat[prefix + k] = v
        return flat

    def parse_json_from_db(self, raw_json):
        """
        Parse safely a JSON field from the database, which may be:
        - a dict (already parsed),
        - a string (to be parsed),
        - or invalid.
        """
        if isinstance(raw_json, dict):
            return [raw_json]  # retorna como lista, se for um único dict
        elif isinstance(raw_json, list):
            return raw_json
        elif isinstance(raw_json, str):
            try:
                return json.loads(raw_json.strip())
            except json.JSONDecodeError as e:
                print(f"[ERRO] Falha ao carregar JSON: {e}")
                return []
        else:
            print(f"[ERRO] Tipo inesperado: {type(raw_json)}")
            return []
   
    def __load_commits(self) -> None:
        """Load commits."""
        self.logger.info("Loading commits...")
        for commit in self.commits.itertuples(index=False):
            data = self.transform(commit)
            data["id"] = data["sha"]
            self.logger.debug("Commit transformed: %s", data["id"])

            try:
               combined = {**data, **commit.commit}
                
            except Exception as e:
                self.logger.warning(f"Invalid commit JSON for {commit.sha}: {e}")
                continue

            node_data = {**data, **self.flatten_dict(combined, "")}
            node = self.create_node(node_data, COMMIT, "id")

            repository_node = self.get_node(SOURCEREPOSITORY, full_name=commit.repository)

            if repository_node:
                self.create_relationship(repository_node, HAS, node)
                # self.create_relationship(node, PRESENT_IN, repository_node)
            else:
                self.logger.warning(
                    "Repository not found for commit: %s", 
                    commit.repository
                )
            
            # Author
            if commit.author:
                author = commit.author
                login = author["login"]
                user_node = self.get_node(PERSON, id=login)
                
                if user_node:
                    self.create_relationship(node, CREATED_BY, user_node)
                    self.logger.debug(
                        f"Linked author {login} to commit {commit.sha}"
                    )
                else:
                    self.logger.warning(f"Author not found: {login}")
                    author["id"] = login
                    author["name"] = login

                    person_node = self.create_node(author, PERSON, "id")
                    self.create_relationship(person_node, PRESENT_IN, self.organization_node)
                    self.create_relationship(node, CREATED_BY, person_node)
                    self.logger.info(
                        f"Linked author {login} to commit {commit.sha}"
                    )
            
            # Committer
            if commit.committer:
                committer = commit.committer
                login = committer["login"]
                user_node = self.get_node(PERSON, id=login)
                if user_node:
                    self.create_relationship(node, COMMITTED_BY, user_node)
                    self.logger.debug(
                        f"Linked committer {login} to commit {commit.sha}"
                    )
                else:
                    self.logger.warning(f"Committer not found: {login}")
                    committer["id "]= login
                    committer["name"] = login

                    person_node = self.create_node(committer, PERSON, "id")
                    self.create_relationship(person_node, PRESENT_IN, self.organization_node)
                    self.create_relationship(node, COMMITTED_BY, person_node)
                    self.logger.info(
                        f"Linked committer {login} to commit {commit.sha}"
                    )
            # Branch
            branch_id = commit.branch + "-" + commit.repository
            branch_node = self.get_node(BRANCH, id=branch_id)
            if branch_node:
                self.create_relationship(branch_node, HAS, node)
                # self.create_relationship(node, IN, branch_node)
                self.logger.debug(f"Linked commit {commit.sha} to branch {branch_id}")
            else:
                self.logger.warning(f"Branch not found: {branch_id}")
            
            ## Busca os arquivos do commit e cria os SoftwareArtifact
            # process_commit.delay(sha=commit.sha, repository=commit.repository, secret=self.secret)
            

    def __create_relation_commits(self) -> None:
        
        """Create parent relationships between commits."""
        self.logger.info("Creating parent relationships between commits...")
        for commit in self.commits.itertuples(index=False):
            parents = commit.parents
            
            for parent in parents:
                commit_node = self.get_node(COMMIT, id=commit.sha)
                parent_node = self.get_node(COMMIT, id=parent["sha"])
                if commit_node and parent_node:
                    self.create_relationship(parent_node, IS_PARENT, commit_node)
                    #self.create_relationship(commit_node, HAS_PARENT, parent_node)
                    self.logger.debug(f"Linked {parent['sha']} -> {commit.sha}")
                else:
                    self.logger.info(
                        "Missing node for parent-child relation: %s ->  %s",
                        parent["sha"],
                        commit.sha,
                    )
                
    def __load_branchs(self) -> None:
        """Load branches."""
        self.logger.info("Loading branches...")
        for branch in self.branches.itertuples(index=False):
            data = self.transform(branch)
            data["id"] = data["name"] + "-" + data["repository"]
            self.logger.debug("Branch transformed: %s", data["id"])

            node = self.create_node(data, BRANCH, "id")

            if branch.repository:
                repository_node = self.get_node(
                    SOURCEREPOSITORY, full_name=branch.repository
                )
                if repository_node:
                    self.create_relationship(repository_node, HAS, node)
                    self.logger.info(
                        f"Linked branch {data['id']} to repository {branch.repository}"
                    )
                else:
                    self.logger.warning(
                        f"Repository not found for branch: {branch.repository}"
                    )

    def run(self) -> None:
        """Run the full extraction and persistence process."""
        self.logger.info("🔄 Starting CMPO extraction...")
        self.fetch_data()
        self.__load_source_code()
        self.__load_repository_project()
        self.__load_branchs()
        self.__load_commits()
        self.__create_relation_commits()
        self.create_config_domain("cmpo")
        self.logger.info("✅ CMPO extraction completed.")
        return "done"