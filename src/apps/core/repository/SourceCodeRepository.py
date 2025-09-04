from .base import Neo4jRepository



class SourceCodeRepository(Neo4jRepository):

   
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

    
    
    
    