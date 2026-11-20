"""A1: confirm the missed injected guarantee from saved and fresh evidence. Read-only, CPU only.

Run from the repository root:  PYTHONPATH=. python3 evaluation/m4_20261127/rq3/baseline/confirm_negative_control.py

negative_control_confirmation.json was produced with Critic 0.4.0 at the baseline commit, before task A3.
negative_control_after_A3.json is the same script run with Critic 0.5.0.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
import critic
from critic import contract as K, llm as L
from critic.critic import CRITIC_VERSION
ROOT = Path('.')
FX = ROOT / 'integration/fixtures/one_pass_20261113'
A = FX / 'artifacts/models'
manifest = json.loads((FX / 'MANIFEST.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = {'purpose': 'A1 confirmation of the missed injected guarantee (negative control). Read-only.',
       'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
       'critic_version': CRITIC_VERSION, 'prompt_version': L.PROMPT_VERSION}
out['fixture_files_match_manifest'] = all(sha(FX / a['file']) == a['sha256'] for a in manifest['artifacts'])
req = json.loads((A / 'critic.controlled-negative.request.json').read_text())
orig = json.loads((A / 'critic.request.json').read_text())
rep = json.loads((A / 'critic.controlled-negative.qwen.report.json').read_text())
target = next(n for g in req['argument_bundle']['graphs'] for n in g['graph']['nodes']
              if n['id'] == 'cream_cheese_1:G1')
out['injected_statement'] = target['statement']
diff = [k for k in req if req[k] != orig[k]]
out['request_fields_differing_from_original'] = diff
out['saved_qwen_report'] = {
    'source': 'saved model output (real Qwen/Qwen3-32B call recorded in the fixture)',
    'sha256': sha(A / 'critic.controlled-negative.qwen.report.json'),
    'review_status': rep['review_status'], 'criticisms': len(rep['criticisms']),
    'rejected_llm_findings': len(rep['rejected_llm_findings']), 'raw_response': rep['llm']['raw_response'],
    'model': rep['llm']['model'], 'request_sha256_matches_request': rep['llm']['request_sha256'] == K.digest(req)}
fresh = critic.review(req)
out['fresh_rule_only_review'] = {
    'source': 'deterministic Critic rules, run now (no model)', 'review_status': fresh['review_status'],
    'criticisms': len(fresh['criticisms'])}
reply = {'findings': [{'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1', 'category': 'C12',
                       'severity': 'high',
                       'explanation': ('The goal states "' + target['statement']
                                       + '" and nothing in the package supports a guarantee.'),
                       'evidence_ids': [], 'suggested_action': 'Remove the guarantee.'}]}
scripted = critic.review(req, L.ScriptedLLM(json.dumps(reply)))
out['scripted_screen_diagnostic'] = {
    'source': 'scripted reply written for this check; NOT a model detection',
    'accepted': [(c['check_id'], c['category'], c['node_id']) for c in scripted['criticisms']],
    'rejected': len(scripted['rejected_llm_findings'])}
print(json.dumps(out, indent=2, ensure_ascii=False))
