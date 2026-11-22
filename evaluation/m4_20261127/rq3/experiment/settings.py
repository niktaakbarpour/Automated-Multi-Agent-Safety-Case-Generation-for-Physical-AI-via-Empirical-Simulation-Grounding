"""Frozen settings of the RQ3 model-only runs (M4 task A3).

Model and decoding settings repeat those of the saved Nov 13 one-pass Qwen Critic call
(integration/fixtures/one_pass_20261113/artifacts/models/critic.qwen.report.json, llm.settings), so that the
experiment uses the configuration the team already ran. They are the same for T, R and C. The model revision
(checkpoint) and the hardware are recorded by the runner at run time; they are not known here.
"""
BATCH_VERSION = 'rq3-batch/0.1.0'
REPEATS = 3
SETTINGS = {
    'model': 'Qwen/Qwen3-32B',
    'temperature': 0.6,
    'max_tokens': 8192,
    'timeout_s': 600,
    'extra_body': {'top_p': 0.95, 'top_k': 20, 'response_format': {'type': 'json_object'},
                   'chat_template_kwargs': {'enable_thinking': False}},
    'seed': None,
    'source': 'integration/fixtures/one_pass_20261113/artifacts/models/critic.qwen.report.json (llm.settings)',
}
