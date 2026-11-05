"""Offline local-model transport checks; no model or project evidence is sent.

The HTTP server binds only to an ephemeral loopback port. Responses are test
messages, not executed LLM results or safety arguments.
"""
from contextlib import contextmanager
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch

from drafter.llm import (
    ConfigError,
    FrozenLocalModelConfig,
    LocalModelClient,
    load_local_model_config,
)


MODEL = "offline-test-model"
MESSAGES = [{"role": "user", "content": "Return a connection-test response."}]
PROBE_SCHEMA = {
    "type": "object",
    "properties": {"connected": {"const": True}},
    "required": ["connected"],
    "additionalProperties": False,
}


def configuration(base_url="http://127.0.0.1:12345/v1", **overrides):
    value = {
        "schema_version": "drafter-local-model/0.1.0",
        "base_url": base_url,
        "model_id": MODEL,
        "model_revision": None,
        "timeout_seconds": 1.0,
        "max_tokens": 128,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 123,
        "response_format": "json_schema",
        "api_key_env": None,
        "allow_remote_endpoint": False,
        "max_response_bytes": 4096,
    }
    value.update(overrides)
    return value


def completion(**overrides):
    value = {
        "id": "offline-chat-completion",
        "model": MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": '{"connected":true}'},
            "finish_reason": "stop",
        }],
    }
    value.update(overrides)
    return value


@contextmanager
def fake_endpoint():
    state = {
        "requests": [],
        "discovery_body": {"data": [{"id": MODEL}, {"id": "other-offline-model"}]},
        "completion_body": completion(),
        "status": 200,
        "delay": 0,
        "headers": {},
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format, *args):
            pass

        def respond(self):
            request_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            state["requests"].append({
                "method": self.command,
                "path": self.path,
                "headers": dict(self.headers.items()),
                "body": json.loads(request_body) if request_body else None,
            })
            time.sleep(state["delay"])
            value = state["discovery_body"] if self.command == "GET" else state["completion_body"]
            raw = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
            try:
                self.send_response(state["status"])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                for key, val in state["headers"].items():
                    self.send_header(key, val)
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                # A timed-out client is expected to close the socket first.
                pass

        do_GET = respond
        do_POST = respond

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    state["base_url"] = f"http://127.0.0.1:{server.server_port}/v1"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class ModelConfigurationTests(unittest.TestCase):
    def test_optional_enable_thinking_preserves_existing_configurations(self):
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).resolve().parents[1] / "schemas/local_model.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for settings in ({}, {"enable_thinking": None}, {"enable_thinking": False},
                         {"enable_thinking": True}):
            with self.subTest(settings=settings):
                value = configuration(**settings)
                self.assertEqual(list(validator.iter_errors(value)), [])
                config = FrozenLocalModelConfig.from_mapping(value)
                self.assertIs(config.enable_thinking, settings.get("enable_thinking"))

    def test_invalid_enable_thinking_is_rejected_by_schema_and_config(self):
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).resolve().parents[1] / "schemas/local_model.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for thinking in (0, 1, "false", "true", "none", [], {}):
            with self.subTest(enable_thinking=thinking):
                value = configuration(enable_thinking=thinking)
                self.assertTrue(list(validator.iter_errors(value)))
                with self.assertRaises(ConfigError):
                    FrozenLocalModelConfig.from_mapping(value)

    def test_optional_reasoning_effort_preserves_existing_configurations(self):
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).resolve().parents[1] / "schemas/local_model.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for settings in ({}, {"reasoning_effort": None}, {"reasoning_effort": "none"},
                         {"reasoning_effort": "low"}, {"reasoning_effort": "medium"},
                         {"reasoning_effort": "high"}):
            with self.subTest(settings=settings):
                value = configuration(**settings)
                self.assertEqual(list(validator.iter_errors(value)), [])
                config = FrozenLocalModelConfig.from_mapping(value)
                self.assertEqual(config.reasoning_effort, settings.get("reasoning_effort"))

    def test_invalid_reasoning_effort_is_rejected_by_schema_and_config(self):
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).resolve().parents[1] / "schemas/local_model.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for effort in ([], {}, True, False, 0, "automatic", "NONE", ""):
            with self.subTest(reasoning_effort=effort):
                value = configuration(reasoning_effort=effort)
                self.assertTrue(list(validator.iter_errors(value)))
                with self.assertRaises(ConfigError):
                    FrozenLocalModelConfig.from_mapping(value)

    def test_config_file_roundtrip_preserves_settings(self):
        value = configuration()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "local-model.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            config = load_local_model_config(path)
        self.assertEqual(config.model_id, MODEL)
        self.assertEqual(config.response_format, "json_schema")
        self.assertEqual(config.max_tokens, 128)
        self.assertEqual(config.seed, 123)

    def test_bad_urls_are_rejected_before_network(self):
        for url in (
            "file:///private/model",
            "ftp://127.0.0.1/v1",
            "http://user:password@127.0.0.1:12345/v1",
            "http://127.0.0.1:12345/v1?api_key=embedded",
            "http://127.0.0.1:12345/v1#fragment",
            "http://remote.example/v1",
            "http://127.0.0.1:70000/v1",
        ):
            with self.subTest(url=url), self.assertRaises(ConfigError):
                FrozenLocalModelConfig.from_mapping(configuration(base_url=url))

    def test_remote_endpoint_needs_explicit_opt_in(self):
        config = FrozenLocalModelConfig.from_mapping(configuration(
            base_url="https://model.example/v1", allow_remote_endpoint=True))
        self.assertTrue(config.allow_remote_endpoint)

    def test_numeric_bounds_and_types_are_enforced(self):
        invalid = (
            ("timeout_seconds", 0), ("timeout_seconds", 301),
            ("timeout_seconds", float("nan")), ("timeout_seconds", True),
            ("timeout_seconds", 10**400), ("temperature", 10**400), ("top_p", 10**400),
            ("temperature", float("inf")), ("temperature", -0.1), ("temperature", 2.1),
            ("temperature", True), ("top_p", True),
            ("top_p", 0), ("top_p", 1.1), ("top_p", float("nan")),
            ("max_tokens", 0), ("max_tokens", 16385), ("max_tokens", True),
            ("max_tokens", "128"), ("seed", True), ("seed", -1),
            ("max_response_bytes", 127), ("max_response_bytes", 4194305),
            ("max_response_bytes", True), ("allow_remote_endpoint", "false"),
        )
        for field, value in invalid:
            with self.subTest(field=field, value=value), self.assertRaises(ConfigError):
                FrozenLocalModelConfig.from_mapping(configuration(**{field: value}))

    def test_required_and_unknown_configuration_fields_are_enforced(self):
        missing = configuration()
        del missing["model_id"]
        for value in (missing, configuration(unknown_option=True), configuration(api_key_env="bad env name")):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                FrozenLocalModelConfig.from_mapping(value)


class LocalModelTransportTests(unittest.TestCase):
    def client(self, state, **overrides):
        config = FrozenLocalModelConfig.from_mapping(configuration(state["base_url"], **overrides))
        return LocalModelClient(config)

    def assert_failed(self, result):
        self.assertEqual(result.status, "error")
        self.assertTrue(result.error_code)
        self.assertTrue(result.message)

    def test_model_discovery_uses_models_endpoint(self):
        with fake_endpoint() as state:
            result = self.client(state).discover_models()
            self.assertEqual(result.status, "ok")
            self.assertEqual(set(result.model_ids), {MODEL, "other-offline-model"})
            request = state["requests"][0]
            self.assertEqual((request["method"], request["path"]), ("GET", "/v1/models"))

    def test_discovery_does_not_choose_an_unconfigured_model(self):
        with fake_endpoint() as state:
            state["discovery_body"] = {"data": [{"id": "other-offline-model"}]}
            result = self.client(state).discover_models()
            self.assert_failed(result)
            self.assertFalse(result.configured_model_available)
            self.assertEqual(result.model_ids, ("other-offline-model",))

    def test_json_schema_request_and_successful_completion(self):
        with fake_endpoint() as state:
            result = self.client(state).complete(MESSAGES, PROBE_SCHEMA, schema_name="connection_probe")
            self.assertEqual(result.status, "ok")
            self.assertEqual(json.loads(result.text), {"connected": True})
            self.assertEqual(result.finish_reason, "stop")
            self.assertEqual(result.effective_model_id, MODEL)
            self.assertRegex(result.request_sha256, r"^[0-9a-f]{64}$")
            self.assertRegex(result.response_sha256, r"^[0-9a-f]{64}$")
            request = state["requests"][0]
            self.assertEqual((request["method"], request["path"]), ("POST", "/v1/chat/completions"))
            body = request["body"]
            self.assertEqual(body["model"], MODEL)
            self.assertEqual(body["messages"], MESSAGES)
            self.assertEqual(body["max_tokens"], 128)
            self.assertFalse(body["stream"])
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertEqual(body["response_format"]["json_schema"]["name"], "connection_probe")
            self.assertEqual(body["response_format"]["json_schema"]["schema"], PROBE_SCHEMA)

    def test_reasoning_effort_is_sent_only_when_explicitly_requested(self):
        for settings in ({}, {"reasoning_effort": None}, {"reasoning_effort": "none"}):
            with self.subTest(settings=settings), fake_endpoint() as state:
                result = self.client(state, **settings).complete(MESSAGES, PROBE_SCHEMA)
                self.assertEqual(result.status, "ok")
                body = state["requests"][0]["body"]
                if settings.get("reasoning_effort") is None:
                    self.assertNotIn("reasoning_effort", body)
                else:
                    self.assertEqual(body["reasoning_effort"], "none")

    def test_enable_thinking_is_sent_only_for_explicit_boolean_settings(self):
        for settings in ({}, {"enable_thinking": None}, {"enable_thinking": False},
                         {"enable_thinking": True}):
            with self.subTest(settings=settings), fake_endpoint() as state:
                result = self.client(state, **settings).complete(MESSAGES, PROBE_SCHEMA)
                self.assertEqual(result.status, "ok")
                body = state["requests"][0]["body"]
                if settings.get("enable_thinking") is None:
                    self.assertNotIn("chat_template_kwargs", body)
                else:
                    self.assertEqual(body["chat_template_kwargs"], {
                        "enable_thinking": settings["enable_thinking"],
                    })

    def test_supported_response_format_modes_have_correct_payloads(self):
        for response_format in ("json_object", "vllm_structured_outputs"):
            with self.subTest(response_format=response_format), fake_endpoint() as state:
                result = self.client(state, response_format=response_format).complete(MESSAGES, PROBE_SCHEMA)
                self.assertEqual(result.status, "ok")
                body = state["requests"][0]["body"]
                if response_format == "json_object":
                    self.assertEqual(body["response_format"], {"type": "json_object"})
                else:
                    self.assertEqual(body["structured_outputs"], {"json": PROBE_SCHEMA})

    def test_api_key_is_read_from_environment_and_excluded_from_results(self):
        name, secret = "DRAFTER_TEST_API_KEY", "offline-only-secret-value"
        with patch.dict(os.environ, {name: secret}), fake_endpoint() as state:
            client = self.client(state, api_key_env=name)
            result = client.complete(MESSAGES, PROBE_SCHEMA)
            self.assertEqual(result.status, "ok")
            headers = {k.lower(): v for k, v in state["requests"][0]["headers"].items()}
            self.assertEqual(headers.get("authorization"), "Bearer " + secret)
            self.assertNotIn(secret, json.dumps(asdict(result)))
            self.assertNotIn(secret, repr(client.config))
            self.assertNotIn(secret, json.dumps(state["requests"][0]["body"]))

    def test_success_response_redacts_a_json_escaped_server_secret_echo(self):
        name, secret = "DRAFTER_TEST_API_KEY", 'offline-"quoted"-\\key'
        schema = {
            "type": "object", "properties": {"connected": {"const": True}, "note": {"type": "string"}},
            "required": ["connected", "note"], "additionalProperties": False,
        }
        with patch.dict(os.environ, {name: secret}), fake_endpoint() as state:
            state["completion_body"] = completion(debug=secret)
            state["completion_body"]["choices"][0]["message"]["content"] = json.dumps({
                "connected": True, "note": secret,
            })
            result = self.client(state, api_key_env=name).complete(MESSAGES, schema)
            self.assertEqual(result.status, "ok")
            self.assertTrue(result.response_redacted)
            self.assertNotEqual(result.parsed_json["note"], secret)
            self.assertNotIn(secret, result.raw_response["debug"])
            self.assertNotIn(json.dumps(secret)[1:-1], result.text)

    def test_missing_configured_api_key_fails_without_network(self):
        name = "DRAFTER_TEST_MISSING_API_KEY"
        with patch.dict(os.environ, {}, clear=False), fake_endpoint() as state:
            os.environ.pop(name, None)
            client = self.client(state, api_key_env=name)
            for result in (client.discover_models(), client.complete(MESSAGES, PROBE_SCHEMA)):
                self.assert_failed(result)
                self.assertEqual(result.error_code, "missing_api_key")
            self.assertEqual(state["requests"], [])

    def test_malformed_discovery_response_returns_error(self):
        for body in ([], {}, {"data": [{"id": []}]}, b"not JSON"):
            with self.subTest(body=body), fake_endpoint() as state:
                state["discovery_body"] = body
                self.assert_failed(self.client(state).discover_models())

    def test_malformed_completion_envelopes_return_error(self):
        for body in (
            [], {}, {"model": MODEL, "choices": []}, {"model": MODEL, "choices": {}},
            b"not JSON", completion(model=[]),
        ):
            with self.subTest(body=body), fake_endpoint() as state:
                state["completion_body"] = body
                result = self.client(state).complete(MESSAGES, PROBE_SCHEMA)
                self.assert_failed(result)
                self.assertIsNone(result.text)

    def test_content_and_choice_types_are_checked(self):
        choices = (
            ["not-a-choice-object"],
            [{"message": [], "finish_reason": "stop"}],
            [{"message": {"content": ["not-a-string"]}, "finish_reason": "stop"}],
            [{"message": {"content": None}, "finish_reason": "stop"}],
            [{"message": {"content": ""}, "finish_reason": "stop"}],
            [{"message": {"content": "   "}, "finish_reason": "stop"}],
        )
        for value in choices:
            with self.subTest(choices=value), fake_endpoint() as state:
                state["completion_body"] = completion(choices=value)
                self.assert_failed(self.client(state).complete(MESSAGES, PROBE_SCHEMA))

    def test_invalid_structured_content_is_not_a_successful_completion(self):
        for text in ("not JSON", "[]", '{"connected":NaN}', '{"connected":true,"connected":false}'):
            with self.subTest(text=text), fake_endpoint() as state:
                state["completion_body"] = completion()
                state["completion_body"]["choices"][0]["message"]["content"] = text
                self.assert_failed(self.client(state).complete(MESSAGES, PROBE_SCHEMA))

    def test_wrong_returned_model_is_not_silently_accepted(self):
        with fake_endpoint() as state:
            state["completion_body"] = completion(model="unexpected-model")
            self.assert_failed(self.client(state).complete(MESSAGES, PROBE_SCHEMA))

    def test_truncated_and_unfinished_responses_are_not_successes(self):
        for reason in ("length", "content_filter", None):
            with self.subTest(reason=reason), fake_endpoint() as state:
                state["completion_body"] = completion()
                state["completion_body"]["choices"][0]["finish_reason"] = reason
                self.assert_failed(self.client(state).complete(MESSAGES, PROBE_SCHEMA))

    def test_timeout_returns_explicit_error_without_retry(self):
        with fake_endpoint() as state:
            state["delay"] = 0.25
            result = self.client(state, timeout_seconds=0.05).complete(MESSAGES, PROBE_SCHEMA)
            self.assert_failed(result)
            self.assertEqual(len(state["requests"]), 1)

    def test_http_error_is_contained_and_secret_is_redacted(self):
        name, secret = "DRAFTER_TEST_API_KEY", "offline-only-secret-value"
        with patch.dict(os.environ, {name: secret}), fake_endpoint() as state:
            state["status"] = 500
            state["completion_body"] = {"error": {"message": "server echoed " + secret}}
            result = self.client(state, api_key_env=name).complete(MESSAGES, PROBE_SCHEMA)
            self.assert_failed(result)
            self.assertNotIn(secret, json.dumps(asdict(result)))
            self.assertEqual(len(state["requests"]), 1)

    def test_redirect_is_rejected_without_following_it(self):
        with fake_endpoint() as state:
            state["status"] = 302
            state["headers"] = {"Location": state["base_url"] + "/must-not-follow"}
            result = self.client(state).complete(MESSAGES, PROBE_SCHEMA)
            self.assert_failed(result)
            self.assertEqual(len(state["requests"]), 1)
            self.assertNotIn("must-not-follow", state["requests"][0]["path"])

    def test_oversized_completion_and_discovery_responses_are_rejected(self):
        with fake_endpoint() as state:
            state["completion_body"] = completion(large_padding="x" * 2000)
            state["discovery_body"] = {"data": [{"id": "x" * 2000}]}
            client = self.client(state, max_response_bytes=512)
            self.assert_failed(client.complete(MESSAGES, PROBE_SCHEMA))
            self.assert_failed(client.discover_models())

    def test_invalid_requests_fail_before_network(self):
        invalid_messages = ([], "not-a-message-list", [{"role": "user", "content": []}])
        with fake_endpoint() as state:
            client = self.client(state)
            for messages in invalid_messages:
                with self.subTest(messages=messages), self.assertRaises(ConfigError):
                    client.complete(messages, PROBE_SCHEMA)
            with self.assertRaises(ConfigError):
                client.complete(MESSAGES, [])
            self.assertEqual(state["requests"], [])


if __name__ == "__main__":
    unittest.main()
