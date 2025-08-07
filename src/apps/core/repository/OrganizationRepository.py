from .base import Neo4jRepository



class OrganizationRepository(Neo4jRepository):
    
    STATS_ISSUES_STATUS_ORGANIZATION = """
MATCH (:Organization)-[:has]->(:Repository)-[:has]->(:Milestone)-[:has]->(i:Issue)
WHERE i.state IS NOT NULL

WITH
  COUNT(CASE WHEN i.state = "open" THEN 1 END) AS opened_issues,
  COUNT(CASE WHEN i.state = "closed" THEN 1 END) AS closed_issues
WITH
  opened_issues,
  closed_issues,
  (opened_issues + closed_issues) AS total_issues,
  CASE
    WHEN (opened_issues + closed_issues) > 0 THEN
      ROUND(toFloat(closed_issues) / (opened_issues + closed_issues) * 100, 2)
    ELSE 0
  END AS completion_percentage
RETURN
  opened_issues AS `Abertas`,
  closed_issues AS `Fechadas`,
  total_issues AS `Total`,
  completion_percentage AS ` %`

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

    STATS_ORGANIZATION_WEEK = """
// Busca issues com data de criação ou fechamento
MATCH (:Organization)-[:has]->(:Repository)-[:has]->(:Milestone)-[:has]->(i:Issue)
WHERE i.closed_at IS NOT NULL OR i.created_at IS NOT NULL

// Processa separadamente as datas válidas
WITH
  CASE WHEN i.created_at IS NOT NULL 
       THEN date.truncate('week', date(datetime(REPLACE(i.created_at, " ", "T")))) 
       ELSE NULL 
  END AS created_week,
  
  CASE WHEN i.closed_at IS NOT NULL 
       THEN date.truncate('week', date(datetime(REPLACE(i.closed_at, " ", "T")))) 
       ELSE NULL 
  END AS closed_week

// Concatena eventos de criação e fechamento
WITH 
  COLLECT({week: created_week, type: "open"}) + 
  COLLECT({week: closed_week, type: "closed"}) AS events
UNWIND events AS e
WITH e.week AS week_start, e.type AS type
WHERE week_start IS NOT NULL

// Contagem por tipo de evento por semana
WITH
  week_start,
  COUNT(CASE WHEN type = "open" THEN 1 END) AS opened_issues,
  COUNT(CASE WHEN type = "closed" THEN 1 END) AS closed_issues
WITH
  week_start,
  opened_issues,
  closed_issues,
  (opened_issues + closed_issues) AS total_issues,
  CASE 
    WHEN (opened_issues + closed_issues) > 0 THEN 
      ROUND(toFloat(closed_issues) / (opened_issues + closed_issues) * 100, 2)
    ELSE 0
  END AS completion_percentage,
  closed_issues AS velocity
RETURN 
  toString(week_start) AS week_start,
  opened_issues,
  closed_issues,
  total_issues,
  completion_percentage AS `percent_completed`,
  velocity
ORDER BY week_start


"""

    
    def get_all_feature_milestone(self,skip: int = 0, limit: int = 10):
        """ Retrive all feature from milestone from repositories"""
        raw_data = self.execute(self.ALL_FEATURES_IN_MILESTONE, skip=skip, limit=limit)
        return raw_data
    
    