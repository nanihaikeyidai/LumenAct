"""Standalone localhost reference server; no imports from Lumen or Motive."""
import argparse
import json
from pathlib import Path
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener, urlopen
import webbrowser

from download_assets import asset_issues, load_manifest
import voice_services

ROOT = Path(__file__).resolve().parent


class SemanticModel:
    """Plain ONNX classification. No behavior scheduler or director policy."""

    def __init__(self):
        self.config = json.loads((ROOT / "models/semantic/config.json").read_text(encoding="utf-8"))
        self.ready = False
        self.error = ""
        self.lock = threading.RLock()

    def ensure(self):
        with self.lock:
            if self.ready:
                return
            if self.error:
                raise RuntimeError(self.error)
            try:
                import numpy as np
                import onnxruntime as ort
                from tokenizers import Tokenizer
                base = ROOT / "models" / "semantic"
                self.np = np
                self.tokenizer = Tokenizer.from_file(str(base / self.config["tokenizer_file"]))
                self.tokenizer.enable_truncation(max_length=int(self.config["max_length"]))
                self.session = ort.InferenceSession(
                    str(base / self.config["model_file"]), providers=["CPUExecutionProvider"])
                self.ready = True
            except Exception as exc:
                self.error = (
                    "本地语义模型无法加载。请运行 install_semantic.bat / install_semantic.sh 后重启。"
                    if isinstance(exc, ImportError) else "本地语义模型加载失败：" + str(exc))
                raise RuntimeError(self.error) from exc

    def warmup(self):
        try:
            self.predict("自然放松", "你好")
        except Exception as exc:
            self.ready = False
            self.error = self.error or "本地语义模型预热失败：" + str(exc)

    def predict(self, intent, text=""):
        self.ensure()
        started = time.perf_counter()
        with self.lock:
            encoded = self.tokenizer.encode(intent, text)
            fields = {"input_ids": encoded.ids, "attention_mask": encoded.attention_mask,
                      "token_type_ids": encoded.type_ids}
            feed = {item.name: self.np.asarray([fields[item.name]], dtype=self.np.int64)
                    for item in self.session.get_inputs()}
            outputs = [value[0] for value in self.session.run(None, feed)]
        catalog = self.config["catalog"]

        def rank(logits, names):
            values = self.np.asarray(logits, dtype=self.np.float64)
            probabilities = self.np.exp(values - values.max())
            probabilities /= probabilities.sum()
            return sorted(({"name": name, "score": float(probabilities[i]), "index": i}
                           for i, name in enumerate(names)), key=lambda item: -item["score"])

        labels = rank(outputs[0], catalog["labels"])
        context_names = ["auto"] + [item["context_id"] for item in catalog["contexts"]]
        contexts = rank(outputs[1], context_names)
        context = contexts[0]
        # The reference player uses the top category, then a compatible context.
        # There are no copied confidence gates, behavior rules, or expression policies.
        context_data = None if context["index"] == 0 else catalog["contexts"][context["index"] - 1]
        if context_data and context_data["label"] != labels[0]["name"]:
            context_data = None
        voice = rank(outputs[2], catalog["speech_styles"])[0]
        return {
            "model": self.config["name"], "device": "CPU",
            "expression": labels[0]["name"], "confidence": labels[0]["score"],
            "context_id": context_data["context_id"] if context_data else "auto",
            "context_name": context_data.get("subcategory", "") if context_data else "",
            "speech_style": voice["name"], "top_labels": labels[:5],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "operation": "semantic_selection",
        }


def forward_service(body, speech=False):
    endpoint = str(body.get("endpoint", "")).strip()
    parsed = urlsplit(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
        raise ValueError("请输入完整的 http(s) 服务 Endpoint")
    headers = {"Content-Type": "application/json"}
    if body.get("key"):
        headers["Authorization"] = "Bearer " + str(body["key"])
    if speech:
        payload = {"model": body.get("model") or "tts-1", "input": str(body.get("text", "")),
                   "voice": body.get("voice") or "alloy", "response_format": "mp3"}
    else:
        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages 不能为空")
        payload = {"model": body.get("model") or None, "messages": messages}
        if payload["model"] is None:
            payload.pop("model")
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    open_request = (build_opener(ProxyHandler({})).open
                    if parsed.hostname in ("127.0.0.1", "localhost", "::1") else urlopen)
    try:
        with open_request(request, timeout=90) as response:
            content = response.read(64 * 1024 * 1024 + 1)
            if len(content) > 64 * 1024 * 1024:
                raise ValueError("服务响应超过 64MB")
            return content, response.headers.get_content_type()
    except HTTPError as exc:
        # Do not echo request URLs, keys, request bodies, or provider diagnostics.
        raise RuntimeError(f"服务返回 HTTP {exc.code}，请检查 Endpoint、模型和密钥") from exc
    except URLError as exc:
        raise RuntimeError("无法连接到配置的服务，请检查地址与服务状态") from exc


def handler_type(semantic, service_defaults=None, voice=None):
    voice = voice or voice_services.VoiceConfig()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def send_bytes(self, status, content, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, status, value):
            self.send_bytes(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/health":
                self.send_json(200, {"ready": semantic.ready, "error": semantic.error,
                                     "model": semantic.config["name"], "device": "CPU"})
            elif path == "/api/services/config":
                defaults = voice.public()
                defaults.update({key: value for key, value in (service_defaults or {}).items() if value != ""})
                self.send_json(200, defaults)
            elif path == "/":
                self.send_response(302)
                self.send_header("Location", "/preview/")
                self.end_headers()
            elif path.startswith("/api/"):
                self.send_json(404, {"error": "没有这个接口"})
            else:
                super().do_GET()

        def do_POST(self):
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                self.send_json(403, {"error": "只接受当前本地预览页的请求"})
                return
            try:
                path = urlsplit(self.path).path
                length = int(self.headers.get("Content-Length", "0"))
                # 录音上传需要更大的请求体；其余接口保持 256KB 上限。
                limit = 24 * 1024 * 1024 if path == "/api/services/transcribe" else 256 * 1024
                if not 0 < length <= limit:
                    raise ValueError("请求体为空或超过 " + ("24MB" if limit > 256 * 1024 else "256KB"))
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("请求体必须是 JSON 对象")
                if path == "/api/semantic":
                    intent, text = str(body.get("intent", "")).strip(), str(body.get("text", ""))
                    if not intent:
                        raise ValueError("请输入情绪描述")
                    self.send_json(200, semantic.predict(intent[:2000], text[:4000]))
                elif path == "/api/services/chat":
                    content, kind = forward_service(voice.fill_service(body, "llm"))
                    self.send_bytes(200, content, kind)
                elif path == "/api/services/speech":
                    # backend: runninghub / indextts-local / openai（缺省，兼容旧请求）
                    content, kind = voice_services.synthesize(voice, body)
                    self.send_bytes(200, content, kind)
                elif path == "/api/services/transcribe":
                    self.send_json(200, voice_services.transcribe(voice, body))
                else:
                    self.send_json(404, {"error": "没有这个接口"})
            except (ValueError, KeyError, TypeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except Exception as exc:
                self.send_json(503, {"error": str(exc)})

        def log_message(self, format, *args):
            pass  # No endpoint URLs, API keys, or chat content are written to logs.

    return Handler


def main():
    parser = argparse.ArgumentParser(description="LumenAct 本地参考预览")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--services-profile", type=Path,
                        help="Optional external JSON file with non-secret service defaults")
    args = parser.parse_args()
    missing = asset_issues(ROOT, load_manifest()['artifacts'], verify_hash=False)
    if missing:
        names = '\n'.join('  ' + name for name, _ in missing)
        raise SystemExit('缺少资源或资源大小不符：\n' + names +
                         '\n请先运行 python download_assets.py --repo OWNER/REPOSITORY --revision COMMIT_OR_TAG。\n'
                         '已配置发布仓库时可省略 --repo 和 --revision；完整即用包自带资源。')
    service_defaults = {}
    if args.services_profile:
        profile = json.loads(args.services_profile.read_text(encoding="utf-8-sig"))
        if not isinstance(profile, dict):
            raise SystemExit("Service profile must be a JSON object")
        for name in ("llmEndpoint", "llmModel", "ttsEndpoint", "ttsModel", "ttsVoice"):
            if isinstance(profile.get(name), str):
                service_defaults[name] = profile[name]
        if isinstance(profile.get("ttsEnabled"), bool):
            service_defaults["ttsEnabled"] = profile["ttsEnabled"]
        for name in ("ttsBackend", "asrBackend", "asrEndpoint", "asrModel", "asrLanguage"):
            if isinstance(profile.get(name), str):
                service_defaults[name] = profile[name]
        for name in ("autoListen", "lipSync", "listenReaction", "captions"):
            if isinstance(profile.get(name), bool):
                service_defaults[name] = profile[name]
    else:
        profile = {}
    voice = voice_services.VoiceConfig(profile)
    semantic = SemanticModel()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port),
                                     handler_type(semantic, service_defaults, voice))
    except OSError as exc:
        raise SystemExit(f"端口 {args.port} 不可用，可使用 --port 指定其他端口。") from exc
    threading.Thread(target=semantic.warmup, daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/preview/"
    print("LumenAct reference preview:", url, flush=True)
    print("语音对话 TTS 默认后端:", voice.tts_backend, "| ASR 默认后端:", voice.asr_backend, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
