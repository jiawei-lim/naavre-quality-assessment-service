from django.conf import settings
from github import Github, Auth


def get_raw_file(url: str) -> str:
    parts = url.replace("https://github.com/", "").split("/")
    owner, repo, _, ref = parts[0], parts[1], parts[2], parts[3]
    path = "/".join(parts[4:])

    auth = Auth.Token(settings.GITHUB_PAT)
    github = Github(auth=auth)
    repository = github.get_repo(f"{owner}/{repo}")
    content = repository.get_contents(path, ref=ref)

    return content.decoded_content.decode()

