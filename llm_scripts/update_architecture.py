import argparse
import os
import re
import requests
from pathlib import Path

def design_with_llm(issue_title, issue_body):
    LLM_URL = "http://localhost:11434/api/generate"  # ton serveur LLM local
    MODEL = "llama3"  # adapte selon ton modèle
    OUTPUT_FILE = Path("docs/ecs_architecture.puml")

    # --- Prompt LLM ---
    prompt = f"""
    You are an AI software architect designing a C++ ECS (Entity-Component-System) architecture
    for a Computer Generated Forces (CGF) simulation.

    Analyze the following issue and output PlantUML code describing:
    - Components (data containers)
    - Systems (logic that processes Components)
    - Relationships: System --> Component dependencies

    Output ONLY valid PlantUML content between @startuml and @enduml.
    Group logically by package ("Components", "Systems").

    Issue title: {issue_title}
    Issue body:
    {issue_body}
    """

    # --- Appel au LLM ---
    response = requests.post(
        LLM_URL,
        json={"model": MODEL, "prompt": prompt},
    )

    if response.status_code != 200:
        raise RuntimeError(f"LLM request failed: {response.text}")

    data = response.json()
    llm_output = data.get("response") or data.get("text") or ""

    if "@startuml" not in llm_output or "@enduml" not in llm_output:
        raise ValueError("LLM did not return valid PlantUML code.")

    # --- Extraction du contenu généré ---
    new_content = re.search(r"@startuml(.*?)@enduml", llm_output, re.S)
    if not new_content:
        raise ValueError("No PlantUML body found.")
    new_body = new_content.group(1)

    # --- Lecture du fichier existant ---
    existing_body = ""
    if OUTPUT_FILE.exists():
        text = OUTPUT_FILE.read_text(encoding="utf-8")
        match = re.search(r"@startuml(.*?)@enduml", text, re.S)
        if match:
            existing_body = match.group(1)

    # --- Extraction des éléments existants ---
    def extract_elements(body: str):
        classes = set(re.findall(r"\bclass\s+(\w+)", body))
        relations = set(re.findall(r"(\w+)\s+-->\s+(\w+)", body))
        return classes, relations

    existing_classes, existing_relations = extract_elements(existing_body)
    new_classes, new_relations = extract_elements(new_body)

    # --- Fusion des éléments ---
    merged_classes = existing_classes | new_classes
    merged_relations = existing_relations | new_relations

    # --- Reconstruire le diagramme ---
    def format_classes(classes, group_name):
        lines = [f'package "{group_name}" {{']
        for c in sorted(classes):
            if group_name == "Components" and not c.endswith("System"):
                lines.append(f"  class {c}")
            elif group_name == "Systems" and c.endswith("System"):
                lines.append(f"  class {c}")
        lines.append("}")
        return "\n".join(lines)

    components_text = format_classes(merged_classes, "Components")
    systems_text = format_classes(merged_classes, "Systems")
    relations_text = "\n".join(f"{a} --> {b}" for a, b in sorted(merged_relations))

    merged_body = f"{components_text}\n\n{systems_text}\n\n{relations_text}"

    # --- Écriture finale ---
    final_text = f"@startuml\n{merged_body}\n@enduml\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(final_text, encoding="utf-8")

    print("✅ ECS architecture diagram merged and updated successfully.")

# --- Configuration ---
issue_title = os.getenv("ISSUE_TITLE", "")
issue_body = os.getenv("ISSUE_BODY", "")

def main():
    parser = argparse.ArgumentParser(description="Update ECS architecture diagram based on issue.")
    parser.add_argument("--title", required=False, help="Title of the issue")
    parser.add_argument("--body", required=False, help="Body/description of the issue")
    args = parser.parse_args()

    issue_title = args.title
    issue_body = args.body

    print(f"🧩 Processing issue: {issue_title}")
    print(f"Description: {issue_body[:100]}...")


