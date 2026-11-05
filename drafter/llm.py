"""Bounded, explicit local-model transport; no automatic model deployment.

Requests use the OpenAI-compatible /models and /chat/completions endpoints.
Nothing automatically supplies project evidence, follows redirects, retries, picks
another model, installs weights, or interprets the result as a physical assessment.
"""
from dataclasses import asdict, dataclass
import hashlib
from http.client import HTTPException
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


CONFIG_VERSION = 'drafter-local-model/0.1.0'
CONFIG_FIELDS = frozenset({
    'schema_version', 'base_url', 'model_id', 'model_revision', 'timeout_seconds',
    'max_tokens', 'temperature', 'top_p', 'seed', 'response_format', 'api_key_env',
    'allow_remote_endpoint', 'max_response_bytes',
})
RESPONSE_FORMATS = ('json_schema', 'json_object', 'vllm_structured_outputs')
REASONING_EFFORTS = ('none', 'low', 'medium', 'high')


class ConfigError(ValueError):
    """Local configuration/request failure, before any network call."""
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(code + ': ' + message)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _strict_json(value):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = item
        return result
    def constant(_):
        raise ValueError('Nonfinite JSON')
    result = json.loads(value, object_pairs_hook=pairs, parse_constant=constant)
    _canonical(result)
    return result


def _text(value, field, maximum=512):
    if (not isinstance(value, str) or not value or value != value.strip()
            or len(value) > maximum or any(ord(c) < 32 for c in value)):
        raise ConfigError('invalid_configuration', field + ' must be a nonempty bounded string.')


def _number(value, field, low, high, include_low=True):
    if (type(value) not in (int, float) or value > high
            or (value < low if include_low else value <= low) or not math.isfinite(value)):
        raise ConfigError('invalid_configuration', field + ' is outside its finite bounds.')


def _base_url(value, allow_remote):
    _text(value, 'base_url', 2048)
    try:
        parsed = urlsplit(value)
        host, port = parsed.hostname, parsed.port
        if (not value.startswith(('http://', 'https://')) or parsed.scheme not in ('http', 'https') or not host or not parsed.netloc
                or parsed.username is not None or parsed.password is not None
                or '?' in value or '#' in value or '%' in parsed.netloc
                or parsed.query or parsed.fragment or (port is not None and not 1 <= port <= 65535)
                or any(c.isspace() for c in value)):
            raise ValueError('Endpoint structure')
        decoded_path = unquote(parsed.path)
        if any(ord(c) < 32 for c in decoded_path) or '..' in decoded_path.split('/'):
            raise ValueError('Endpoint path')
    except (ValueError, TypeError):
        raise ConfigError('invalid_endpoint', 'Use an HTTP(S) model-server base URL without credentials, query or fragment.') from None
    host = host.lower().rstrip('.')
    # A local transport must not silently become a paid OpenAI/Azure API client.
    if (host == 'openai.com' or host.endswith('.openai.com')
            or host == 'openai.azure.com' or host.endswith('.openai.azure.com')):
        raise ConfigError('hosted_provider_disabled', 'Paid OpenAI/Azure model endpoints are disabled.')
    try:
        address = ipaddress.ip_address(host)
        loopback = address.is_loopback or (address.version == 6 and address.ipv4_mapped is not None and address.ipv4_mapped.is_loopback)
    except ValueError:
        loopback = host == 'localhost'
    if not loopback and not allow_remote:
        raise ConfigError('remote_endpoint_requires_opt_in', 'A team-hosted endpoint requires explicit allow_remote_endpoint=true.')
    return value.rstrip('/')


@dataclass(frozen=True)
class FrozenLocalModelConfig:
    schema_version: str
    base_url: str
    model_id: str
    model_revision: str | None
    timeout_seconds: float
    max_tokens: int
    temperature: float
    top_p: float
    seed: int | None
    response_format: str
    api_key_env: str | None
    allow_remote_endpoint: bool
    max_response_bytes: int
    reasoning_effort: str | None = None
    enable_thinking: bool | None = None

    def __post_init__(self):
        if self.schema_version != CONFIG_VERSION:
            raise ConfigError('invalid_configuration', 'Unsupported local-model configuration version.')
        if type(self.allow_remote_endpoint) is not bool:
            raise ConfigError('invalid_configuration', 'allow_remote_endpoint must be boolean.')
        object.__setattr__(self, 'base_url', _base_url(self.base_url, self.allow_remote_endpoint))
        _text(self.model_id, 'model_id')
        if self.model_revision is not None:
            _text(self.model_revision, 'model_revision')
        _number(self.timeout_seconds, 'timeout_seconds', 0, 300, False)
        _number(self.temperature, 'temperature', 0, 2)
        _number(self.top_p, 'top_p', 0, 1, False)
        if type(self.max_tokens) is not int or not 1 <= self.max_tokens <= 16384:
            raise ConfigError('invalid_configuration', 'max_tokens must be an integer from 1 through 16384.')
        if type(self.max_response_bytes) is not int or not 128 <= self.max_response_bytes <= 4194304:
            raise ConfigError('invalid_configuration', 'max_response_bytes must be an integer from 128 through 4194304.')
        if self.seed is not None and (type(self.seed) is not int or not 0 <= self.seed <= 2147483647):
            raise ConfigError('invalid_configuration', 'seed must be null or a bounded nonnegative integer.')
        if not isinstance(self.response_format, str) or self.response_format not in RESPONSE_FORMATS:
            raise ConfigError('invalid_configuration', 'Choose an explicit supported response_format.')
        if self.reasoning_effort is not None and (not isinstance(self.reasoning_effort, str)
                or self.reasoning_effort not in REASONING_EFFORTS):
            raise ConfigError('invalid_configuration', 'reasoning_effort must be null, none, low, medium or high.')
        if self.enable_thinking is not None and type(self.enable_thinking) is not bool:
            raise ConfigError('invalid_configuration', 'enable_thinking must be null or boolean.')
        if self.api_key_env is not None and (not isinstance(self.api_key_env, str)
                or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', self.api_key_env)):
            raise ConfigError('invalid_configuration', 'api_key_env must be null or an environment-variable name, never a key value.')

    @classmethod
    def from_mapping(cls, value):
        if (not isinstance(value, dict) or not CONFIG_FIELDS <= set(value)
                or not set(value) <= CONFIG_FIELDS | {'reasoning_effort', 'enable_thinking'}):
            raise ConfigError('invalid_configuration', 'Configuration has missing or unexpected fields.')
        return cls(**value)

    def public_settings(self):
        """Configuration only; an optional environment name is not its secret value."""
        return asdict(self)


def load_local_model_config(path):
    """Read only the explicit user-selected configuration path, bounded to 64 KiB."""
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError('Configuration too large')
        value = _strict_json(raw.decode('utf-8'))
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        raise ConfigError('configuration_unavailable', 'Cannot read a finite, bounded local-model configuration.') from None
    return FrozenLocalModelConfig.from_mapping(value)


@dataclass(frozen=True)
class ModelDiscoveryResult:
    status: str
    model_ids: tuple[str, ...] = ()
    configured_model_available: bool = False
    error_code: str | None = None
    message: str | None = None
    request_sha256: str | None = None
    response_sha256: str | None = None
    raw_response: dict[str, Any] | None = None
    response_redacted: bool = False


@dataclass(frozen=True)
class CompletionResult:
    status: str
    text: str | None = None
    raw_response: dict[str, Any] | None = None
    parsed_json: dict[str, Any] | None = None
    finish_reason: str | None = None
    effective_model_id: str | None = None
    error_code: str | None = None
    message: str | None = None
    request_sha256: str | None = None
    response_sha256: str | None = None
    response_redacted: bool = False


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def _redact(value, secret):
    if not secret:
        return value
    if isinstance(value, str):
        for representation in (secret, json.dumps(secret, ensure_ascii=False)[1:-1],
                               json.dumps(secret, ensure_ascii=True)[1:-1]):
            value = value.replace(representation, '[REDACTED]')
        return value
    if isinstance(value, list):
        return [_redact(v, secret) for v in value]
    if isinstance(value, dict):
        return {_redact(k, secret): _redact(v, secret) for k, v in value.items()}
    return value


class LocalModelClient:
    def __init__(self, config):
        if not isinstance(config, FrozenLocalModelConfig):
            raise ConfigError('invalid_configuration', 'A validated FrozenLocalModelConfig is required.')
        self.config = config
        # No environment proxies: requests go only to the configured model endpoint.
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _request(self, suffix, payload=None):
        url = self.config.base_url + suffix
        method = 'GET' if payload is None else 'POST'
        body = None if payload is None else _canonical(payload)
        request_sha = _sha(_canonical({'method': method, 'url': url, 'body': payload}))
        common = {'request_sha256': request_sha, 'response_sha256': None,
                  'raw_response': None, 'response_redacted': False}
        headers = {'Accept': 'application/json'}
        secret = None
        if self.config.api_key_env is not None:
            secret = os.environ.get(self.config.api_key_env)
            if not secret or '\r' in secret or '\n' in secret:
                return {**common, 'error_code': 'missing_api_key', 'message': 'The configured authentication environment variable is unavailable or invalid.'}
            headers['Authorization'] = 'Bearer ' + secret
        if body is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(self.config.max_response_bytes + 1)
                if len(raw) > self.config.max_response_bytes:
                    return {**common, 'error_code': 'response_too_large', 'message': 'The model-server response exceeded its configured byte limit.'}
            common['response_sha256'] = _sha(raw)
            value = _strict_json(raw.decode('utf-8'))
            if not isinstance(value, dict):
                return {**common, 'error_code': 'invalid_response_shape', 'message': 'The model server must return a JSON object.'}
            sanitized = _redact(value, secret)
            common.update(raw_response=sanitized, response_redacted=sanitized != value)
            return common
        except HTTPError as error:
            code = error.code
            error.close()
            return {**common, 'error_code': 'redirect_rejected' if 300 <= code < 400 else 'http_error', 'message': 'Model server returned HTTP ' + str(code) + '; no retry or redirect was performed.'}
        except (socket.timeout, TimeoutError):
            return {**common, 'error_code': 'timeout', 'message': 'The model-server request timed out.'}
        except URLError as error:
            timeout = isinstance(error.reason, (socket.timeout, TimeoutError))
            return {**common, 'error_code': 'timeout' if timeout else 'connection_error', 'message': 'The model server could not be reached.'}
        except (UnicodeError, ValueError, TypeError, RecursionError):
            return {**common, 'error_code': 'invalid_json_response', 'message': 'The model-server response was not finite, valid UTF-8 JSON.'}
        except OSError:
            return {**common, 'error_code': 'connection_error', 'message': 'The model-server connection failed.'}
        except HTTPException:
            return {**common, 'error_code': 'invalid_http_response', 'message': 'The model server returned an incomplete or malformed HTTP response.'}

    def discover_models(self):
        """Check the explicit model ID; never choose another advertised model."""
        result = self._request('/models')
        if result.get('error_code'):
            return ModelDiscoveryResult(status='error', **result)
        data = result['raw_response'].get('data')
        if (not isinstance(data, list) or any(not isinstance(item, dict)
                or not isinstance(item.get('id'), str) or not item['id'].strip() for item in data)):
            return ModelDiscoveryResult(status='error', error_code='invalid_models_response', message='The model list has an unexpected structure.', **result)
        model_ids = tuple(item['id'] for item in data)
        available = self.config.model_id in model_ids
        return ModelDiscoveryResult(status='ok' if available else 'error', model_ids=model_ids,
                                    configured_model_available=available,
                                    error_code=None if available else 'configured_model_unavailable',
                                    message=None if available else 'The configured model is not advertised; no fallback was chosen.', **result)

    def complete(self, messages, json_schema, schema_name='smoke_probe'):
        """Transport an explicit JSON-object request, without automatic retries.

        The caller separately validates parsed_json against the requested schema.
        The response digest binds original bytes; returned content is secret-redacted.
        """
        if (not isinstance(messages, list) or not 1 <= len(messages) <= 32
                or any(not isinstance(m, dict) or set(m) != {'role', 'content'}
                       or m['role'] not in ('system', 'user', 'assistant')
                       or not isinstance(m['content'], str) or not m['content'].strip() for m in messages)):
            raise ConfigError('invalid_request', 'Provide a bounded list of explicit role/content messages.')
        if (not isinstance(json_schema, dict) or not isinstance(schema_name, str)
                or not re.fullmatch('[A-Za-z0-9_-]{1,64}', schema_name)):
            raise ConfigError('invalid_request', 'A JSON schema object and bounded schema name are required.')
        payload = {'model': self.config.model_id, 'messages': messages, 'stream': False,
                   'n': 1, 'max_tokens': self.config.max_tokens,
                   'temperature': self.config.temperature, 'top_p': self.config.top_p}
        if self.config.seed is not None:
            payload['seed'] = self.config.seed
        if self.config.reasoning_effort is not None:
            payload['reasoning_effort'] = self.config.reasoning_effort
        if self.config.enable_thinking is not None:
            payload['chat_template_kwargs'] = {'enable_thinking': self.config.enable_thinking}
        if self.config.response_format == 'json_schema':
            payload['response_format'] = {'type': 'json_schema', 'json_schema': {
                'name': schema_name, 'strict': True, 'schema': json_schema}}
        elif self.config.response_format == 'json_object':
            payload['response_format'] = {'type': 'json_object'}
        else:
            payload['structured_outputs'] = {'json': json_schema}
        try:
            if len(_canonical(payload)) > 262144:
                raise ValueError('Request too large')
        except (ValueError, TypeError, RecursionError):
            raise ConfigError('invalid_request', 'The request must be finite bounded JSON.') from None
        result = self._request('/chat/completions', payload)
        if result.get('error_code'):
            return CompletionResult(status='error', **result)
        value = result['raw_response']
        model, choices = value.get('model'), value.get('choices')
        if not isinstance(model, str) or model != self.config.model_id:
            return CompletionResult(status='error', error_code='model_mismatch', message='The returned model does not match the configured model.', **result)
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            return CompletionResult(status='error', effective_model_id=model, error_code='invalid_completion_shape', message='Exactly one completion choice is required.', **result)
        choice = choices[0]
        finish = choice.get('finish_reason')
        common = {**result, 'effective_model_id': model,
                  'finish_reason': finish if isinstance(finish, str) else None}
        if finish != 'stop':
            return CompletionResult(status='error', error_code='incomplete_completion', message='The completion did not finish normally; truncated or alternative output is not accepted.', **common)
        message = choice.get('message')
        if (not isinstance(message, dict) or message.get('role', 'assistant') != 'assistant'
                or message.get('tool_calls') or message.get('refusal')
                or not isinstance(message.get('content'), str) or not message['content'].strip()):
            return CompletionResult(status='error', error_code='invalid_completion_content', message='A nonempty assistant text response without tool calls or refusal is required.', **common)
        text = message['content']
        try:
            parsed = _strict_json(text)
            if not isinstance(parsed, dict):
                raise ValueError('JSON object required')
        except (ValueError, TypeError, RecursionError):
            return CompletionResult(status='error', text=text, error_code='invalid_completion_json', message='The completion content must be a finite JSON object.', **common)
        return CompletionResult(status='ok', text=text, parsed_json=parsed, **common)
