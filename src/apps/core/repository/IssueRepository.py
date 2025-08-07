from .base import Neo4jRepository



class IssueRepository(Neo4jRepository):

    ALL_ISSUES_FROM_MILETONE  = """
        MATCH (r:Repository)-[:has]->(m:Milestone)-[:has]->(i:Issue)
        RETURN 
        r.name AS repository, 
        m.title AS milestone, 
        COLLECT(i.title) AS issues
        ORDER BY r.name, m.title"    
    """

    ALL_FEATURES_IN_MILESTONE="""
        MATCH (r:Repository)-[:has]->(m:Milestone)-[:has]->(i:Issue)
        WHERE TOLOWER(i.title) CONTAINS "feature"
        RETURN 
        r.name AS repository, 
        m.title AS milestone, 
        COLLECT({
            title: i.title, 
            status: i.state, 
            closed_at: i.closed_at
        }) AS issues
        ORDER BY r.name, m.title
    """

    ALL_ISSUE_REPOSITORY="""
      MATCH (r:Repository)-[:has]->(i:Issue)
      WITH r.name AS repo_name, i.state AS state, count(i) AS total_issues_by_state

      CALL {
        MATCH (r2:Repository)-[:has]->(i2:Issue)
        WITH r2.name AS repo_name_inner, count(i2) AS total_issues_repo
        RETURN repo_name_inner, total_issues_repo
      }

      WITH repo_name, state, total_issues_by_state, repo_name_inner, total_issues_repo
      WHERE repo_name = repo_name_inner
      RETURN 
        repo_name AS repository,
        state,
        total_issues_by_state,
        total_issues_repo,
        round(toFloat(total_issues_by_state) / total_issues_repo * 100, 2) AS percentage
      ORDER BY repository, percentage DESC
      SKIP $skip
      LIMIT $limit
      """


    def get_all_issue_repositories(self, skip: int = 0, limit: int = 10):
      
        raw_data = self.execute(self.ALL_ISSUE_REPOSITORY, skip=skip, limit=limit)

        # Agrupando e reestruturando o resultado
        grouped_data = {}
        for item in raw_data:
            repo = item["repository"]
            if repo not in grouped_data:
                grouped_data[repo] = {
                    "repository": repo,
                    "total_issues_repo": item["total_issues_repo"],
                    "issues": []
                }

            grouped_data[repo]["issues"].append({
                "state": item["state"],
                "total_issues_by_state": item["total_issues_by_state"],
                "percentage": item["percentage"]
            })

        return list(grouped_data.values())

    def get_all_milestone_repository(self,skip: int = 0, limit: int = 10):
        """ Retrive milestone from repositories"""
        raw_data = self.execute(self.ALL_ISSUES_FROM_MILETONE, skip=skip, limit=limit)
        return raw_data
    
    def get_all_feature_milestone(self,skip: int = 0, limit: int = 10):
        """ Retrive all feature from milestone from repositories"""
        raw_data = self.execute(self.ALL_FEATURES_IN_MILESTONE, skip=skip, limit=limit)
        return raw_data
    
    