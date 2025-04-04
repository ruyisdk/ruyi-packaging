from github import Github
import os
from checkers.db_models import CheckInfoElement, CheckResultElement
from checkers.checker_base import CheckerBase

class GitHubReleaseChecker(CheckerBase):
    # Initialize the GitHub client (assuming you have a token)
    github_client = Github(os.getenv('GITHUB_TOKEN'))

    def check(self, data: CheckInfoElement) -> CheckResultElement:
        try:
            # Access the repository using segments from the URL
            url = data.check_path
            segments = url.replace("https://", "").split("/")

            repo_owner = segments[1]
            repo_name = segments[2]
            
            # Get the latest release
            repository = self.github_client.get_repo(f"{repo_owner}/{repo_name}")
            self.github_client.per_page = 1
            latest = repository.get_releases()[0]
            
            if latest is None:
                return CheckResultElement(data.name, "", failed=True)

            # Compare if the current tag matches the latest release tag
            #if segments[5] == latest.tag_name:
            #    return CheckResultElement(CheckStatus.AlreadyNewest, latest.html_url, data)
            
            # You may want to add more handling here for newer versions
            return CheckResultElement(data.name, latest.html_url, failed=False)
            
        except Exception as e:
            return CheckResultElement(data.name, "", failed=True)
