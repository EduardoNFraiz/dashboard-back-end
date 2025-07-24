from .base import Neo4jRepository

class IssueRepository(Neo4jRepository):
    def get_all(self, skip: int = 0, limit: int = 10):
        query = f"""
        MATCH (r:Repository)-[:has]->(i:Issue)
        WITH r.name AS repo_name, i.state AS state, count(i) AS total_issues_by_state

        CALL {{
          MATCH (r2:Repository)-[:has]->(i2:Issue)
          WITH r2.name AS repo_name_inner, count(i2) AS total_issues_repo
          RETURN repo_name_inner, total_issues_repo
        }}

        WITH repo_name, state, total_issues_by_state, repo_name_inner, total_issues_repo
        WHERE repo_name = repo_name_inner
        RETURN 
          repo_name AS repository,
          state,
          total_issues_by_state,
          total_issues_repo,
          round(toFloat(total_issues_by_state) / total_issues_repo * 100, 2) AS percentage
        ORDER BY repo_name, percentage DESC
        SKIP $skip
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, skip=skip, limit=limit)
            return [record.data() for record in result]
