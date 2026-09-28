import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import evaluate


def test_shared_metrics_are_calculated_once(monkeypatch):
    for name, score in [('f1_score', 0.6), ('clarity', 0.8), ('precision', 1.0)]:
        monkeypatch.setattr(evaluate, 'evaluate_' + name, Mock(return_value={'score': score}))
    result = evaluate.evaluate_metrics(
        SimpleNamespace(outputs={'answer': 'answer'}, error=None),
        SimpleNamespace(inputs={'bug_report': 'bug'}, outputs={'reference': 'reference'}),
    )
    scores = {item['key']: item['score'] for item in result['results']}
    assert scores == {'f1_score': 0.6, 'clarity': 0.8, 'precision': 1.0, 'helpfulness': 0.9, 'correctness': 0.8}
    for name in ['f1_score', 'clarity', 'precision']:
        getattr(evaluate, 'evaluate_' + name).assert_called_once_with('bug', 'answer', 'reference')


@pytest.mark.parametrize('invalid', [None, float('nan'), float('inf'), '0.8'])
def test_invalid_metric_is_reported(monkeypatch, invalid):
    monkeypatch.setattr(evaluate, 'evaluate_f1_score', lambda *args: {'score': invalid})
    with pytest.raises(ValueError, match='Nota inválida'):
        evaluate.evaluate_metrics(
            SimpleNamespace(outputs={'answer': 'answer'}),
            SimpleNamespace(inputs={}, outputs={}),
        )


@pytest.mark.parametrize('missing', [False, True])
def test_terminal_uses_experiment_feedback(monkeypatch, missing):
    monkeypatch.setattr(evaluate, 'pull_prompt_from_langsmith', Mock())
    monkeypatch.setattr(evaluate, 'get_llm', Mock())
    class Results(list):
        experiment_name = 'test-experiment'
    rows = Results([
        {'evaluation_results': {'results': [
            SimpleNamespace(key=name, score=value)
            for name in evaluate.METRIC_NAMES if not (missing and name == 'correctness')
        ]}}
        for value in [0.6, 0.9]
    ])
    sdk = Mock(return_value=rows)
    monkeypatch.setattr(evaluate, 'langsmith_evaluate', sdk)
    if missing:
        with pytest.raises(ValueError, match='correctness'):
            evaluate.create_langsmith_experiment('prompt', 'dataset', Mock(), 'project')
    else:
        scores = evaluate.create_langsmith_experiment('prompt', 'dataset', Mock(), 'project')
        assert scores == {name: 0.75 for name in evaluate.METRIC_NAMES}
    sdk.assert_called_once()
    assert sdk.call_args.kwargs['num_repetitions'] == 1
    assert sdk.call_args.kwargs['evaluators'] == [evaluate.evaluate_metrics]
