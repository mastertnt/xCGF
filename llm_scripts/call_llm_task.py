import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests

def load_issue(issue_path: Path) -> Any | None:
    if not issue_path.exists():
        return None
    with issue_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"❌ Configuration file not found : {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def reaf_file(path: Path) -> str:
    if not path.exists():
        print(f"⚠️  Design file not found : {path}")
        return ""
    return path.read_text(encoding="utf-8")

def run_llm_task(issue_title, issue_body, config):
    llm_config = config["llm"]
    files_config = config["files"]
    system_prompt_config = config["prompt"]["system"]

    chat_endpoint = f"{llm_config['base_url']}/chat/completions"
    model_name = llm_config['model']
    input_file = Path(files_config["input"])
    output_file = Path(files_config["output"])

    # --- Prompt LLM ---

    issue = f"""
     Issue title: {issue_title}
     Issue body:  {issue_body}
    """
    plantuml = reaf_file(input_file)

    current_architecture = f"""
    The current architecture : {plantuml}
    """

    system_prompt = reaf_file(Path(system_prompt_config))

    payload = {
        "model": model_name,
        "messages":
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": current_architecture},
                {"role": "user", "content": issue}
            ]
    }

    print(f"Sending payload: {payload}")

    # --- Appel au LLM ---
    response = requests.post(
        chat_endpoint,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )

    PAYLOAD_FILE = Path("payload.json")
    PAYLOAD_FILE.write_text(json.dumps(payload), encoding="utf-8")

    print(response.status_code)
    if response.status_code != 200:
        raise RuntimeError(f"LLM request failed: {response.text}")

    resp_json  = response.json()
    llm_output = resp_json["choices"][0]["message"]["content"]

    print(llm_output)

    # --- Écriture finale ---
    #final_text = f"@startuml\n{merged_body}\n@enduml\n"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(llm_output, encoding="utf-8")

    print("✅ ECS architecture diagram merged and updated successfully.")

def main():
    parser = argparse.ArgumentParser(description="ECS LLM.")
    parser.add_argument("--issue", default="architect_issue.json", help="Issue to apply")
    parser.add_argument("--config", default="architect_design.json", help="Path to the configuration JSON file")
    args = parser.parse_args()

    issue = load_issue(Path(args.issue))
    
    if issue is not None:
        issue_title = issue["title"]
        issue_body = issue["body"]
    else:
        issue_title = os.getenv("ISSUE_TITLE", "")
        issue_body = os.getenv("ISSUE_BODY", "")

    config_path = Path(args.config)
    config = load_config(config_path)

    print(config["role"])

    if issue_title and issue_body:
        print(f"🧩 Processing issue: {issue_title}")
        run_llm_task(issue_title, issue_body, config)
        print(f"🏁 Done.")
    else:
        print("⚠️ No issue provided.")


if __name__ == "__main__":
    main()


