"""Model availability and a fixed JSON probe, separate from argument generation."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import time
from pathlib import Path
import uuid

from jsonschema import Draft202012Validator
from evaluation.r1_v4.provenance import digest
from .llm import LocalModelClient

PROBE_VERSION = 'connection-probe/0.1.0'
PROMPT_PATH = Path(__file__).with_name('prompts') / 'connection_probe_v1.md'
PROBE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['probe_id', 'status'],
    'properties': {'probe_id': {'const': 'drafter-connection-v1'}, 'status': {'const': 'ok'}},
}


def check_connection(config, smoke_test=False):
    """Return an inspectable report. No execution evidence is read or sent."""
    started = time.monotonic()
    report = {
        'schema_version': 'drafter-model-connection/0.1.0',
        'run_id': str(uuid.uuid4()), 'started_at': datetime.now(timezone.utc).isoformat(),
        'operation': 'json_smoke_test' if smoke_test else 'model_discovery',
        'status': 'failed', 'configuration': config.public_settings(),
        'configuration_sha256': digest(config.public_settings()),
        'discovery': None, 'completion': None, 'probe': None, 'diagnostics': [],
        'model_called': False, 'argument_generated': False, 'project_evidence_sent': False,
        'empirical_admission_enabled': False, 'safety_claim_verified': False,
    }
    client = LocalModelClient(config)
    discovery = client.discover_models()
    report['discovery'] = asdict(discovery)
    if discovery.status != 'ok':
        report['diagnostics'].append({'code': discovery.error_code, 'message': discovery.message})
    elif not discovery.configured_model_available:
        report['diagnostics'].append({'code': 'configured_model_unavailable',
                                      'message': 'The configured model was not advertised; no fallback was selected.'})
    elif not smoke_test:
        report['status'] = 'ready'
    else:
        prompt = PROMPT_PATH.read_text(encoding='utf-8')
        # Qwen3 supports this documented soft switch; the exact sent text is traced.
        if config.model_id.lower().startswith(('qwen3:', 'qwen/qwen3')):
            prompt += '\n/no_think\n'
        messages = [{'role': 'user', 'content': prompt}]
        report['probe'] = {'version': PROBE_VERSION,
                           'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                           'messages': messages, 'json_schema': PROBE_SCHEMA}
        completion = client.complete(messages, PROBE_SCHEMA, schema_name='drafter_connection_probe')
        reply_received = isinstance(completion.raw_response, dict) and isinstance(completion.raw_response.get('choices'), list)
        report['model_called'] = True if reply_received else None
        report['completion'] = asdict(completion)
        if completion.status != 'ok':
            report['diagnostics'].append({'code': completion.error_code, 'message': completion.message})
        else:
            errors = list(Draft202012Validator(PROBE_SCHEMA).iter_errors(completion.parsed_json))
            if errors:
                report['diagnostics'].append({'code': 'probe_schema_mismatch',
                                              'message': 'The model reply did not match the fixed probe schema.'})
            else:
                report['status'] = 'passed'
    report['elapsed_seconds'] = round(time.monotonic() - started, 6)
    return report
