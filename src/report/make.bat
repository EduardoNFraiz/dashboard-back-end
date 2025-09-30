@echo off
REM === Make.bat: choose one of the options ===
REM Uso: make.bat build|analyse|report

if "%1"=="" (
    echo Uso: make.bat [build|analyse|report]
    goto fim
)

if "%1"=="build" (
    echo Executando criacao...
    python ./criar_relacoes/build_pr_relations.py 
    python ./criar_relacoes/build_tasks_relations.py 
    python ./criar_relacoes/build_roles_properties.py 
    goto fim
)

if "%1"=="analyse" (
    echo Executando analisar...
    python ./community_smells/community_smells_by_teams.py 
    python ./community_smells/community_smells_all.py 
    python ./community_smells/community_smells_all_time.py 
    goto fim
)

if "%1"=="report" (
    echo Executando reports...
    python results_teams.py 
    python results_all.py 
    goto fim
)


echo Ivalid arg: %1
echo Valid Options: build, analyse, report

:fim
