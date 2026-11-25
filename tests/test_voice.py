"""语音对话服务端测试：全部使用 tests/mock_services.py 本地模拟，不访问外网、不消耗点数。"""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mock_services  # noqa: E402
import server  # noqa: E402
import voice_services  # noqa: E402

HEX = "0123456789abcdef0123456789abcdef"
OPEN = build_opener(ProxyHandler({})).open


class DummySemantic:
    ready, error, config = False, "", {"name": "dummy"}


class VoiceServerTests(unittest.TestCase):
    def setUp(self):
        self.mock, self.state = mock_services.start()
        self.base = f"http://127.0.0.1:{self.mock.server_port}"
        self.temp = tempfile.TemporaryDirectory()
        self.ref = Path(self.temp.name) / "ref.wav"
        self.ref.write_bytes(mock_services.tone_wav("参考"))
        self.env = {
            "LUMENACT_LLM_ENDPOINT": self.base + "/v1/chat/completions", "LUMENACT_LLM_KEY": "llm-secret",
            "LUMENACT_TTS_ENDPOINT": self.base + "/v1/audio/speech", "LUMENACT_TTS_KEY": "tts-secret",
            "LUMENACT_ASR_ENDPOINT": self.base + "/v1/audio/transcriptions",
            "RUNNINGHUB_API_KEY": "  " + HEX + "-extra", "LUMENACT_RH_BASE": self.base,
            "LUMENACT_INDEXTTS_REF": str(self.ref), "LUMENACT_INDEXTTS_ENDPOINT": self.base + "/indextts",
            "LUMENACT_TTS_CACHE": str(Path(self.temp.name) / "cache"), "LUMENACT_RH_POLL": "0.01",
        }
        self.patcher = patch.dict(os.environ, self.env)
        self.patcher.start()
        self.voice = voice_services.VoiceConfig()
        self.app = ThreadingHTTPServer(("127.0.0.1", 0), server.handler_type(DummySemantic(), {}, self.voice))
        threading.Thread(target=self.app.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.app.server_port}"

    def tearDown(self):
        self.app.shutdown(); self.app.server_close()
        self.mock.shutdown(); self.mock.server_close()
        self.patcher.stop(); self.temp.cleanup()

    def post(self, path, body):
        request = Request(self.url + path, data=json.dumps(body).encode(), method="POST",
                          headers={"Content-Type": "application/json"})
        with OPEN(request, timeout=30) as response:
            return response.read(), response.headers.get_content_type()

    def requests(self, suffix):
        return [item for item in self.state.requests if item["path"].endswith(suffix)]

    def test_runninghub_key_takes_first_32_hex(self):
        self.assertEqual(voice_services.runninghub_key(), HEX)

    def test_public_config_has_no_secrets_and_defaults_to_runninghub(self):
        content, _ = self.get_config()
        text = content.decode()
        for secret in ("llm-secret", "tts-secret", HEX):
            self.assertNotIn(secret, text)
        value = json.loads(text)
        self.assertEqual(value["ttsBackend"], "runninghub")
        self.assertTrue(value["runninghubReady"])
        self.assertTrue(value["serverKeys"]["llm"])

    def get_config(self):
        with OPEN(self.url + "/api/services/config", timeout=10) as response:
            return response.read(), response.headers.get_content_type()

    def test_server_key_only_sent_to_configured_endpoint(self):
        content, _ = self.post("/api/services/chat", {"messages": [{"role": "user", "content": "我好开心"}]})
        self.assertIn("开心欢快", json.loads(content)["choices"][0]["message"]["content"])
        self.assertEqual(self.requests("/chat/completions")[-1]["headers"].get("Authorization"), "Bearer llm-secret")
        # 同一个模拟服务换一个路径：不是服务端配置的 Endpoint，不能带上服务端密钥。
        self.post("/api/services/chat", {"endpoint": self.base + "/other/chat/completions",
                                         "messages": [{"role": "user", "content": "你好"}]})
        self.assertNotIn("Authorization", self.requests("/other/chat/completions")[-1]["headers"])

    def test_openai_tts_and_cache(self):
        content, kind = self.post("/api/services/speech", {"backend": "openai", "text": "你好呀"})
        self.assertEqual(kind, "audio/wav")
        self.assertTrue(content.startswith(b"RIFF"))
        self.post("/api/services/speech", {"backend": "openai", "text": "你好呀"})
        self.assertEqual(len(self.requests("/audio/speech")), 1, "相同文本应命中缓存")
        self.assertEqual(self.requests("/audio/speech")[0]["headers"].get("Authorization"), "Bearer tts-secret")

    def test_legacy_speech_request_without_backend_still_uses_openai(self):
        content, _ = self.post("/api/services/speech", {"endpoint": self.base + "/v1/audio/speech", "text": "旧接口"})
        self.assertTrue(content.startswith(b"RIFF"))

    def test_runninghub_indextts_flow(self):
        first, kind = self.post("/api/services/speech", {"backend": "runninghub", "text": "第一句。"})
        self.post("/api/services/speech", {"backend": "runninghub", "text": "第二句。"})
        self.assertEqual(kind, "audio/wav")
        self.assertTrue(first.startswith(b"RIFF"))
        self.assertEqual(len(self.requests("/task/openapi/upload")), 1, "参考音色只上传一次")
        create = self.requests("/task/openapi/create")[0]["body"]
        self.assertEqual(create["apiKey"], HEX)
        self.assertEqual(create["workflowId"], "1970149188463980545")
        nodes = {(item["nodeId"], item["fieldName"]): item["fieldValue"] for item in create["nodeInfoList"]}
        self.assertEqual(nodes[("46", "audio")], "api/mock-ref.wav")
        self.assertEqual(nodes[("47", "prompt")], "第一句。")

    def test_local_indextts_endpoint(self):
        content, _ = self.post("/api/services/speech", {"backend": "indextts-local", "text": "本地合成"})
        self.assertTrue(content.startswith(b"RIFF"))
        self.assertEqual(self.requests("/indextts")[0]["body"]["reference_audio"], str(self.ref))

    def test_browser_backend_is_rejected_by_server(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/api/services/speech", {"backend": "browser", "text": "你好"})
        self.assertEqual(error.exception.code, 400)

    def test_transcribe_openai_multipart_and_large_body(self):
        audio = base64.b64encode(b"\0" * 400 * 1024).decode()  # 大于普通接口的 256KB 上限
        content, _ = self.post("/api/services/transcribe", {"backend": "openai", "audio": audio,
                                                            "mime": "audio/webm", "language": "zh"})
        self.assertEqual(json.loads(content)["text"], "我今天有点难过")
        raw = self.requests("/audio/transcriptions")[0]["raw"]
        self.assertIn(b'name="model"', raw)
        self.assertIn(b'name="language"\r\n\r\nzh', raw)
        self.assertIn(b'filename="speech.webm"', raw)

    def test_transcribe_rejects_bad_audio(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/api/services/transcribe", {"backend": "openai", "audio": "!!!"})
        self.assertEqual(error.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
