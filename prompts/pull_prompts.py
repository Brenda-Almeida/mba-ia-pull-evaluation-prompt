import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_ID = "leonanluppi/bug_to_user_story_v1"

load_dotenv()

def pull_prompts_from_langsmith():
    return hub.pull(
        PROMPT_ID,   
        api_key=os.getenv("LANGSMITH_API_KEY"),
        api_url=os.getenv("LANGSMITH_ENDPOINT"),
        )

def serialize_prompt(prompt):
    messages = []

    for message in prompt.messages:
        message_data = {
            "type": message.__class__.__name__,
        }

        if hasattr(message, "prompt"):
            message_data["template"] = message.prompt.template

        messages.append(message_data)

    return {
        "input_variables": prompt.input_variables,
        "messages": messages,
        "metadata": prompt.metadata,
    }
    
def main():
    if not check_env_vars(["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT"]):
        print("Please set the required environment variables in .env file.")
        sys.exit(1)
    try: 
        prompt = pull_prompts_from_langsmith()

        data = {
            "bug_to_user_story_v1": {
                "description": (
                    "Prompt para converter relatos de bugs em User Stories"
                ),
                "system_prompt": prompt.messages[0].prompt.template,
                "user_prompt": prompt.messages[1].prompt.template,
                "version": "v1",
            }
        }
        
        output_path = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"

        if not save_yaml(data, str(output_path)):
            return 1

        print(f"Prompt salvo em: {output_path}")
        return 0
    except Exception as e:
        print(f"Error occurred while pulling prompts: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
