""" Gerando um relatório sobre o percentual de issues por repositorio, aberto e fechados.

# Conta todos os issues de um repositotio
MATCH (r:Repository)-[:has]->(i:Issue)
RETURN r.name AS repository, count(i) AS total_issues
ORDER BY repository, total_issues DESC


MATCH (r:Repository)-[:has]->(i:Issue)
RETURN r.name AS repository, i.state AS status, count(i) AS total_issues
ORDER BY repository, total_issues DESC


MATCH (:Repository)-[:has]->(i:Issue)
WITH i.state AS state, count(i) AS total_issues, 
     sum(count(i)) OVER () AS total_all
RETURN 
  state, 
  total_issues, 
  round((toFloat(total_issues) / total_all) * 100, 2) AS percentage
ORDER BY percentage DESC

## com percentual de cada status

// Contagem por repositório e estado
MATCH (r:Repository)-[:has]->(i:Issue)
WITH r.name AS repo_name, i.state AS state, count(i) AS total_issues_by_state

// Subconsulta para total de issues por repositório
CALL {
  MATCH (r2:Repository)-[:has]->(i2:Issue)
  WITH r2.name AS repo_name_inner, count(i2) AS total_issues_repo
  RETURN repo_name_inner, total_issues_repo
}

// Junta os dados da subconsulta com os da contagem por estado
WITH repo_name, state, total_issues_by_state, repo_name_inner, total_issues_repo
WHERE repo_name = repo_name_inner
RETURN 
  repo_name AS repository,
  state,
  total_issues_by_state,
  total_issues_repo,
  round(toFloat(total_issues_by_state) / total_issues_repo * 100, 2) AS percentage
ORDER BY repo_name, percentage DESC
"""