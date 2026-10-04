import os
import sys

from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data["user_prompt"]),
        ])

        tags = [
            "bug-to-user-story",
            "v2",
            "optimized",
        ]

        description = prompt_data.get(
            "description",
            "Prompt para converter relatos de bugs em User Stories"
        )

        client = Client(
            api_key=os.getenv("LANGSMITH_API_KEY"),
            api_url=os.getenv("LANGSMITH_ENDPOINT"),
        )
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            tags=tags,
            description=description,
        )
        print(f"Prompt '{prompt_name}' publicado com sucesso! URL: {url}")

        return True

    except Exception as error:
        print(f"Erro ao publicar '{prompt_name}': {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    if not isinstance(prompt_data, dict):
        errors.append("O prompt deve ser um dicionário.")
        return False, errors

    required_fields = ["system_prompt", "user_prompt"]

    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório ausente: '{field}'")

        elif not isinstance(prompt_data[field], str):
            errors.append(f"O campo '{field}' deve ser uma string.")

        elif not prompt_data[field].strip():
            errors.append(f"O campo '{field}' não pode estar vazio.")

    return len(errors) == 0, errors


def main():
    print_section_header("Início da Publicação de Prompts")
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        print("Variáveis de ambiente obrigatórias não configuradas.")
        return 1

    prompt_file = "prompts/bug_to_user_story_v2.yml"

    if not os.path.exists(prompt_file):
        print(f"Arquivo não encontrado: {prompt_file}")
        return 1

    try:
        prompts = load_yaml(prompt_file)
    except Exception as error:
        print(f"Erro ao carregar arquivo YAML: {error}")
        return 1

    if not prompts:
        print("Nenhum prompt encontrado no arquivo YAML.")
        return 1

    success_count = 0
    error_count = 0

    for prompt_name, prompt_data in prompts.items():
        is_valid, errors = validate_prompt(prompt_data)

        if not is_valid:
            print("Prompt inválido:")

            for error in errors:
                print(f"   - {error}")

            error_count += 1
            continue

        if push_prompt_to_langsmith(prompt_name, prompt_data):
            success_count += 1
        else:
            error_count += 1
            
    print_section_header("Resumo da Publicação de Prompts")    
    print(f"\nResumo: {success_count} prompts publicados com sucesso, {error_count} falharam.")

    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

