from .tasks import retrieve_github_data, setup_periodic_tasks

def retrive_data(application, organization, secret, user, repository):
    
    if application.lower()=="github":
        retrieve_github_data(organization=organization, secret=secret,repository=repository)
        setup_periodic_tasks(organization=organization, secret=secret,repository=repository)
