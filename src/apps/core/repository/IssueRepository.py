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

    COUNT_ISSUES_BY_REPOSITORY_ORGANIZATION = """
        MATCH (o:Organization)-[:has]->(r:Repository)-[:has]->(i:Issue)
        RETURN 
        o.name AS organization,
        r.name AS repository,
        COUNT(CASE WHEN i.state = "open" THEN 1 END) AS open_issues,
        COUNT(CASE WHEN i.state = "closed" THEN 1 END) AS closed_issues,
        COUNT(i) AS total_issues
        ORDER BY r.name
    """

    STATS_ISSUES_ORGANIZATION_REPOSITORY = """
        MATCH (:Organization)-[:has]->(r:Repository)-[:has]->(i:Issue)
        WHERE i.created_at IS NOT NULL
        WITH 
        r.name AS repository,
        datetime(REPLACE(i.created_at, " ", "T")) AS created_dt,
        // Calcula o início da quinzena
        date.truncate('week', datetime(REPLACE(i.created_at, " ", "T"))) + 
            duration({days: (datetime(REPLACE(i.created_at, " ", "T")).day - 1) / 14 * 14}) AS fortnight_start,
        i.state AS state
        WITH 
        repository,
        fortnight_start,
        fortnight_start + duration({days: 13}) AS fortnight_end,
        COUNT(*) AS total_issues,
        COUNT(CASE WHEN state = "closed" THEN 1 END) AS closed_issues,
        COUNT(CASE WHEN state = "open" THEN 1 END) AS open_issues
        RETURN 
        repository,
        fortnight_start,
        fortnight_end,
        total_issues,
        open_issues,
        closed_issues,
        CASE 
            WHEN total_issues > 0 THEN ROUND(toFloat(closed_issues) / total_issues * 100, 2)
            ELSE 0
        END AS completion_percentage
        ORDER BY repository, fortnight_start
    """

    STATS_REPOSITORY_MILESTONE = """
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


    ### procurando issues com problemas no mapeamento
    """
// Contar issues sem milestone
CALL {
  MATCH (i:Issue)
  WHERE NOT ( (:Milestone)-[:has]->(i) )
  RETURN COUNT(i) AS issues_without_milestone
}

// Contar issues com milestone, mas sem repository
CALL {
  MATCH (i:Issue)<-[:has]-(m:Milestone)
  WHERE NOT ( (:Repository)-[:has]->(m) )
  RETURN COUNT(i) AS issues_without_repository
}

// Contar issues com milestone e repo, mas sem organização
CALL {
  MATCH (i:Issue)<-[:has]-(m:Milestone)<-[:has]-(r:Repository)
  WHERE NOT ( (:Organization)-[:has]->(r) )
  RETURN COUNT(i) AS issues_without_organization
}

// Contar issues totalmente órfãs (não participam do caminho completo)
CALL {
  MATCH (i:Issue)
  WHERE NOT (
    (:Organization)-[:has]->(:Repository)-[:has]->(:Milestone)-[:has]->(i)
  )
  RETURN COUNT(i) AS total_orphan_issues
}

// Contar issues corretamente ligadas a um milestone
CALL {
  MATCH (i:Issue)<-[:has]-(:Milestone)
  RETURN COUNT(i) AS issues_with_milestone
}

// Contar total de issues no grafo
CALL {
  MATCH (i:Issue)
  RETURN COUNT(i) AS total_issues
}

// Retorna todos os dados de auditoria
RETURN 
  total_issues,
  issues_with_milestone,
  issues_without_milestone,
  issues_without_repository,
  issues_without_organization,
  total_orphan_issues
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
    
    