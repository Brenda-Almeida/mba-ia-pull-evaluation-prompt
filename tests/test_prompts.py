import pytest
import yaml
import sys
import re
from pathlib import Path

def load_prompts(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture
def prompt():
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "bug_to_user_story_v2.yml"
    return load_prompts(prompt_path)["bug_to_user_story_v2"]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        assert "system_prompt" in prompt, "O campo system_prompt deve existir."
        assert isinstance(prompt["system_prompt"], str), "system_prompt deve ser uma string."
        assert prompt["system_prompt"].strip(), "system_prompt não pode estar vazio ou conter apenas espaços."

    def test_prompt_has_role_definition(self, prompt):
        instructions = re.split(r"(?im)^\s*#+\s*EXEMPLO\s+\d+", prompt["system_prompt"])[0]
        assert re.search(
            r"\bvocê\s+é\s+(?:um|uma)\s+\w+", instructions, re.IGNORECASE
        ), "O system_prompt deve definir uma persona explícita: 'Você é um/uma ...'."

    def test_prompt_mentions_format(self, prompt):
        instructions = re.split(r"(?im)^\s*#+\s*EXEMPLO\s+\d+", prompt["system_prompt"])[0]
        markdown = re.search(
            r"\b(?:formato|responda\s+em|saída\s+em)\s+markdown\b",
            instructions, re.IGNORECASE,
        )
        user_story = re.search(
            r"User Story\s*:\s*Como\s+.+?,\s*(?:eu\s+)?quero\s+.+?,\s*para\s+.+",
            instructions, re.IGNORECASE | re.DOTALL,
        )
        assert markdown or user_story, "O prompt deve exigir Markdown ou o padrão 'Como..., quero..., para...'."

    def test_prompt_has_few_shot_examples(self, prompt):
        examples = re.split(
            r"(?im)^\s*#+\s*EXEMPLO\s+\d+[^\n]*\n", prompt["system_prompt"]
        )[1:]
        assert len(examples) >= 2, "Few-shot requer pelo menos dois exemplos."
        for index, example in enumerate(examples, 1):
            pair = re.search(
                r"Entrada:\s*(.*?)\s*Saída:\s*(.*)", example, re.IGNORECASE | re.DOTALL
            )
            assert pair and all(part.strip() for part in pair.groups()), (
                f"O exemplo {index} deve conter Entrada e Saída preenchidas."
            )

    def test_prompt_no_todos(self, prompt):
        text = yaml.safe_dump(prompt, allow_unicode=True)
        assert not re.search(r"\[\s*TODO\s*\]", text, re.IGNORECASE), (
            "O prompt contém um marcador [TODO] não resolvido."
        )

    def test_minimum_techniques(self, prompt):
        techniques = prompt.get("techniques_applied")
        assert isinstance(techniques, list), "techniques_applied deve ser uma lista nos metadados do YAML."
        assert all(isinstance(item, str) and item.strip() for item in techniques), (
            "Cada técnica deve ser uma string não vazia."
        )
        assert len({item.strip().casefold() for item in techniques}) >= 2, (
            "Liste pelo menos duas técnicas distintas em techniques_applied."
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
