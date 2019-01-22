import subprocess

def fetch_git_repo(uri, dst_dir):
    """
    Clone the git repo at ``uri`` into ``dst_dir``, checking out commit ``version`` (or defaulting
    to the head commit of the repository's master branch if version is unspecified).
    If ``git_username`` and ``git_password`` are specified, uses them to authenticate while fetching
    the repo. Otherwise, assumes authentication parameters are specified by the environment,
    e.g. by a Git credential helper.
    """
    
    import git
    
    git.Repo.clone_from(uri, dst_dir)