import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

def run(cmd, check=False):
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if check and result.returncode != 0:
        logger.error(result.stderr.strip())
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

def main():
    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    issue_number = os.environ["ISSUE_NUMBER"]
    issue_title = os.environ["ISSUE_TITLE"]
    issue_labels = os.environ.get("ISSUE_LABELS", "[]")
    actor = os.environ.get("GITHUB_ACTOR", "github-actions[bot]")
    commit_message = os.environ.get("COMMIT_MESSAGE", "Automated commit")

    logger.info("Checking repository state...")

    # Get current branch
    current_branch = run("git rev-parse --abbrev-ref HEAD")
    logger.info(f"Current branch: {current_branch}")

    # Show git status
    status = run("git status --porcelain")
    if not status:
        logger.info("No changes detected. Nothing to commit.")
        return

    logger.info("Detected changes:")
    for line in status.splitlines():
        logger.info(f"  {line}")

    # Stage all changes (added, modified, deleted)
    run("git add -A")

    # Configure author if necessary
    run(f'git config user.name "{actor}"')
    run('git config user.email "github-actions@users.noreply.github.com"')

    # Commit and push
    try:
        run(f'git commit -m "{commit_message}"', check=True)
        logger.info("Commit created successfully.")
    except RuntimeError:
        logger.info("No staged changes to commit.")
        return

    # Push to the same branch
    run(f"git push origin {current_branch}", check=True)
    logger.info(f"Changes pushed to branch '{current_branch}'.")

if __name__ == "__main__":
    main()
