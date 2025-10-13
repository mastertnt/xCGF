import os
import re
import json
import logging
from github import Github

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def sanitize_branch_name(name: str) -> str:
    """Convert a string into a safe Git branch name."""
    name = name.lower()
    name = re.sub(r"[^\w\-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:80]  # limit length for safety


def main():
    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    issue_number = os.environ["ISSUE_NUMBER"]
    issue_title = os.environ["ISSUE_TITLE"]
    issue_labels = os.environ.get("ISSUE_LABELS", "[]")

    g = Github(token)
    repo = g.get_repo(repo_name)

    # Determine issue type from labels (default to "task")
    labels = [lbl["name"].lower() for lbl in json.loads(issue_labels)]
    branch_type = "task"
    for label in labels:
        if label in ["bug", "fix"]:
            branch_type = "bugfix"
        elif label in ["feature", "enhancement"]:
            branch_type = "feature"
        elif label in ["chore", "maintenance"]:
            branch_type = "chore"

    # Build branch name
    safe_title = sanitize_branch_name(issue_title)
    branch_name = f"{branch_type}/{issue_number}-{safe_title}"
    base_branch = "master"

    logger.info(f"Creating or switching to branch for issue #{issue_number}: '{branch_name}'")

    # Get the base branch
    try:
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        logger.info(f"Base branch '{base_branch}' found.")
    except Exception as e:
        logger.error(f"Base branch '{base_branch}' not found: {e}")
        exit(1)

    # Check if branch already exists
    try:
        repo.get_git_ref(f"heads/{branch_name}")
        logger.info(f"Branch '{branch_name}' already exists.")
    except Exception:
        logger.info(f"Branch '{branch_name}' does not exist. Creating from '{base_branch}'...")
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)
            logger.info(f"Branch '{branch_name}' created successfully.")
        except Exception as e:
            logger.error(f"Failed to create branch '{branch_name}': {e}")
            exit(1)

    # Verify branch
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
