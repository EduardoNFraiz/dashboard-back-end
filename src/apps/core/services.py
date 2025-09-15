from .tasks import retrieve_github_data, setup_periodic_tasks

def retrive_data(application, organization, secret, user, repository, start_date=None):
    
    if application.lower()=="github":
        retrieve_github_data(organization=organization, secret=secret,repository=repository, start_date=start_date)
        setup_periodic_tasks(organization=organization, secret=secret,repository=repository, start_date=start_date)
