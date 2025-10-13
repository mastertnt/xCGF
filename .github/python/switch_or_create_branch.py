import os
import logging
from github import Github

# Configure console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    branch_name = os.environ.get("BRANCH_NAME")
    base_branch = os.environ.get("BASE_BRANCH")

    if not token or not repo_name or not branch_name or not base_branch:
        logger.error("Missing one or more required environment variables.")
        exit(1)

    logger.info(f"Connecting to GitHub repository '{repo_name}'...")
    g = Github(token)
    repo = g.get_repo(repo_name)

    # Get the base branch
    try:
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        logger.info(f"Base branch '{base_branch}' found.")
    except Exception as e:
        logger.error(f"Base branch '{base_branch}' not found: {e}")
        exit(1)

    # Check if the target branch exists
    try:
        ref = repo.get_git_ref(f"heads/{branch_name}")
        logger.info(f"Branch '{branch_name}' already exists.")
    except Exception:
        logger.info(f"Branch '{branch_name}' does not exist. Creating from '{base_branch}'...")
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)
            logger.info(f"Branch '{branch_name}' created successfully.")
        except Exception as e:
            logger.error(f"Failed to create branch '{branch_name}': {e}")
            exit(1)

    # Confirm the final reference
    try:
        branch_ref = repo.get_git_ref(f"heads/{branch_name}")
        commit = repo.get_commit(branch_ref.object.sha)
        logger.info(
            f"Branch '{branch_name}' now points to commit {commit.sha[:8]} "
            f"({commit.commit.message.splitlines()[0]})."
        )
    except Exception as e:
        logger.error(f"Failed to verify branch '{branch_name}': {e}")
        exit(1)


if __name__ == "__main__":
    main()
