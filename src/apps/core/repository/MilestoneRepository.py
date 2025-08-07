from .base import Neo4jRepository



class MilestoneRepository(Neo4jRepository):

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

    STATS_REPOSITORY_BY_MILESTONE = """
        MATCH (:Organization)-[:has]->(r:Repository)-[:has]->(m:Milestone)-[:has]->(i:Issue)
        WHERE i.state IS NOT NULL AND m.due_on IS NOT NULL
        WITH 
        r.name AS repository,
        m.title AS milestone,
        datetime(REPLACE(m.due_on, " ", "T")) AS due_date,
        COUNT(i) AS total_issues,
        COUNT(CASE WHEN i.state = "closed" THEN 1 END) AS closed_issues,
        COUNT(CASE WHEN i.state = "open" THEN 1 END) AS open_issues
        WITH 
        repository,
        milestone,
        due_date,
        total_issues,
        open_issues,
        closed_issues,
        CASE 
            WHEN total_issues > 0 THEN ROUND(toFloat(closed_issues) / total_issues * 100, 2)
            ELSE 0
        END AS completion_percentage,
        duration.inDays(date(), date(due_date)).days AS days_remaining
        RETURN 
        repository,
        milestone,
        toString(due_date) AS due_date,
        total_issues,
        open_issues,
        closed_issues,
        completion_percentage,
        days_remaining
        ORDER BY repository, milestone

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
    
    