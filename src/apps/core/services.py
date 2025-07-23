from .tasks import retrieve_github_data, setup_periodic_tasks

def retrive_data(organization, secret, repository):
    retrieve_github_data(organization=organization, secret=secret,repository=repository)
    setup_periodic_tasks(organization=organization, secret=secret,repository=repository)
