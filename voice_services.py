"""语音对话的服务端后端：TTS（IndexTTS 2.5 / OpenAI 兼容 / 自建 HTTP）与 ASR（OpenAI 兼容 / 本地 faster-whisper）。

只使用 Python 标准库；faster-whisper 为可选依赖。密钥只从环境变量读取，不写入日志、不返回给网页。
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent
MAX_AUDIO_BYTES = 64 * 1024 * 1024
TTS_BACKENDS = ("runninghub", "indextts-local", "openai", "browser", "off")
ASR_BACKENDS = ("browser", "openai", "local")


def env(name, default=""):
    return os.environ.get(name, default).strip()


def runninghub_key():
    """RUNNINGHUB_API_KEY 可能带有其他字符，取其中第一段 32 位十六进制作为 apiKey。"""
    raw = env("RUNNINGHUB_API_KEY")
    match = re.search(r"[0-9a-fA-F]{32}", raw)
    return match.group(0) if match else raw


def same_endpoint(a, b):
    return bool(a) and bool(b) and a.strip().rstrip("/") == b.strip().rstrip("/")


class VoiceConfig:
    """合并环境变量与 --services-profile（非密钥）配置。网页只能选择后端，不能改服务端路径与密钥。"""

    PROFILE_KEYS = ("ttsBackend", "asrBackend", "asrEndpoint", "asrModel", "asrLanguage",
                    "runninghubBase", "runninghubWorkflowId", "runninghubTextNode", "runninghubTextField",
                    "runninghubAudioNode", "runninghubAudioField", "runninghubRefFileName",
                    "indexttsRefAudio", "indexttsLocalEndpoint", "ttsCacheDir")

    def __init__(self, profile=None):
        profile = profile or {}
        pick = lambda key, name, default="": str(profile.get(key) or env(name, default))
        self.runninghub_base = pick("runninghubBase", "LUMENACT_RH_BASE", "https://www.runninghub.cn").rstrip("/")
        self.workflow_id = pick("runninghubWorkflowId", "LUMENACT_RH_WORKFLOW_ID", "1970149188463980545")
        self.text_node = pick("runninghubTextNode", "LUMENACT_RH_TEXT_NODE", "47")
        self.text_field = pick("runninghubTextField", "LUMENACT_RH_TEXT_FIELD", "prompt")
        self.audio_node = pick("runninghubAudioNode", "LUMENACT_RH_AUDIO_NODE", "46")
        self.audio_field = pick("runninghubAudioField", "LUMENACT_RH_AUDIO_FIELD", "audio")
        self.ref_file_name = pick("runninghubRefFileName", "LUMENACT_RH_REF_FILENAME")
        ref = pick("indexttsRefAudio", "LUMENACT_INDEXTTS_REF")
        self.ref_audio = Path(ref).expanduser() if ref else None
        self.local_endpoint = pick("indexttsLocalEndpoint", "LUMENACT_INDEXTTS_ENDPOINT")
        cache = pick("ttsCacheDir", "LUMENACT_TTS_CACHE", str(ROOT / "voice-cache"))
        self.cache_dir = Path(cache).expanduser()
        self.llm = {"endpoint": env("LUMENACT_LLM_ENDPOINT"), "model": env("LUMENACT_LLM_MODEL"),
                    "key": env("LUMENACT_LLM_KEY")}
        self.tts = {"endpoint": env("LUMENACT_TTS_ENDPOINT"), "model": env("LUMENACT_TTS_MODEL"),
                    "voice": env("LUMENACT_TTS_VOICE"), "key": env("LUMENACT_TTS_KEY")}
        self.asr = {"endpoint": pick("asrEndpoint", "LUMENACT_ASR_ENDPOINT"),
                    "model": pick("asrModel", "LUMENACT_ASR_MODEL"), "key": env("LUMENACT_ASR_KEY"),
                    "language": pick("asrLanguage", "LUMENACT_ASR_LANGUAGE", "zh")}
        tts_backend = pick("ttsBackend", "LUMENACT_TTS_BACKEND")
        if tts_backend not in TTS_BACKENDS:
            tts_backend = ("runninghub" if runninghub_key() and (self.ref_audio or self.ref_file_name)
                           else "openai" if self.tts["endpoint"] else "browser")
        self.tts_backend = tts_backend
        asr_backend = pick("asrBackend", "LUMENACT_ASR_BACKEND", "browser")
        self.asr_backend = asr_backend if asr_backend in ASR_BACKENDS else "browser"
        self.lock = threading.Lock()

    def public(self):
        """返回给网页的默认值：只含后端选择与非密钥字段，以及“服务端已配置密钥”的标记。"""
        return {
            "ttsBackend": self.tts_backend, "asrBackend": self.asr_backend,
            "asrEndpoint": self.asr["endpoint"], "asrModel": self.asr["model"], "asrLanguage": self.asr["language"],
            "llmEndpoint": self.llm["endpoint"], "llmModel": self.llm["model"],
            "ttsEndpoint": self.tts["endpoint"], "ttsModel": self.tts["model"], "ttsVoice": self.tts["voice"],
            "serverKeys": {"llm": bool(self.llm["key"]), "tts": bool(self.tts["key"]),
                           "asr": bool(self.asr["key"]), "runninghub": bool(runninghub_key())},
            "runninghubReady": bool(runninghub_key() and (self.ref_file_name or (self.ref_audio and self.ref_audio.is_file()))),
            "indexttsLocalReady": bool(self.local_endpoint),
        }

    def fill_service(self, body, kind):
        """网页未填 Endpoint/Key 时使用服务端环境配置；服务端密钥只发往服务端配置的同一 Endpoint。"""
        defaults = getattr(self, kind)
        body = dict(body)
        if not str(body.get("endpoint") or "").strip():
            body["endpoint"] = defaults["endpoint"]
        if not body.get("model") and defaults.get("model"):
            body["model"] = defaults["model"]
        if kind == "tts" and not body.get("voice") and defaults.get("voice"):
            body["voice"] = defaults["voice"]
        if not body.get("key") and defaults["key"] and same_endpoint(body["endpoint"], defaults["endpoint"]):
            body["key"] = defaults["key"]
        return body


# ---------------------------------------------------------------- HTTP 工具

def checked_endpoint(endpoint):
    parsed = urlsplit(str(endpoint or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
        raise ValueError("请输入完整的 http(s) 服务 Endpoint")
    return parsed


def open_url(request, timeout=90):
    host = urlsplit(request.full_url).hostname
    opener = build_opener(ProxyHandler({})).open if host in ("127.0.0.1", "localhost", "::1") else urlopen
    return opener(request, timeout=timeout)


def read_limited(response):
    content = response.read(MAX_AUDIO_BYTES + 1)
    if len(content) > MAX_AUDIO_BYTES:
        raise ValueError("服务响应超过 64MB")
    return content


def http_bytes(url, data=None, headers=None, timeout=90, label="服务"):
    request = Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with open_url(request, timeout) as response:
            return read_limited(response), response.headers.get_content_type()
    except HTTPError as exc:
        raise RuntimeError(f"{label}返回 HTTP {exc.code}，请检查 Endpoint、模型和密钥") from exc
    except URLError as exc:
        raise RuntimeError(f"无法连接到{label}，请检查地址与网络") from exc


def post_json(url, payload, timeout=60, label="服务"):
    content, _ = http_bytes(url, json.dumps(payload).encode("utf-8"),
                            {"Content-Type": "application/json"}, timeout, label)
    try:
        return json.loads(content)
    except ValueError as exc:
        raise RuntimeError(f"{label}返回的不是 JSON") from exc


def multipart(fields, files):
    """fields: {name: str}; files: [(name, filename, content_type, bytes)]。"""
    boundary = "----LumenAct" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += str(value).encode("utf-8") + b"\r\n"
    for name, filename, kind, data in files:
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                 f"Content-Type: {kind}\r\n\r\n").encode()
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), "multipart/form-data; boundary=" + boundary


def audio_kind(content, fallback="audio/mpeg"):
    if content[:4] == b"RIFF":
        return "audio/wav"
    if content[:4] == b"fLaC":
        return "audio/flac"
    if content[:4] == b"OggS":
        return "audio/ogg"
    if content[:3] == b"ID3" or content[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio/mpeg"
    return fallback


# ---------------------------------------------------------------- TTS

class SpeechCache:
    """按 (后端, 音色, 文本) 缓存合成结果，同一句话不重复消耗 RunningHub 点数。"""

    def __init__(self, directory):
        self.directory = Path(directory)

    def key(self, *parts):
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:40]

    def get(self, key):
        for path in self.directory.glob(key + ".*"):
            return path.read_bytes(), audio_kind(path.read_bytes())
        return None

    def put(self, key, content, kind):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            suffix = {"audio/wav": ".wav", "audio/flac": ".flac", "audio/ogg": ".ogg"}.get(kind, ".mp3")
            (self.directory / (key + suffix)).write_bytes(content)
        except OSError:
            pass  # 缓存失败不影响播放


class RunningHubIndexTTS:
    """IndexTTS 2.5 RunningHub 工作流：上传参考音色 → create → 轮询 status/outputs → 下载音频。"""

    def __init__(self, config, poll_interval=None, timeout=None):
        self.config = config
        self.poll_interval = float(env("LUMENACT_RH_POLL", "3")) if poll_interval is None else poll_interval
        self.timeout = float(env("LUMENACT_RH_TIMEOUT", "240")) if timeout is None else timeout
        self.upload_index = config.cache_dir / "runninghub-uploads.json"

    def url(self, path):
        return self.config.runninghub_base + path

    def reference_file_name(self, key):
        if self.config.ref_file_name:
            return self.config.ref_file_name
        ref = self.config.ref_audio
        if not ref or not ref.is_file():
            raise RuntimeError("未配置 IndexTTS 参考音色：请设置 LUMENACT_INDEXTTS_REF 指向本地 wav，"
                               "或设置 LUMENACT_RH_REF_FILENAME 为已上传的 RunningHub fileName")
        data = ref.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        with self.config.lock:
            try:
                index = json.loads(self.upload_index.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                index = {}
            if index.get(digest):
                return index[digest]
            body, kind = multipart({"apiKey": key, "fileType": "audio"},
                                   [("file", ref.name, audio_kind(data, "audio/wav"), data)])
            content, _ = http_bytes(self.url("/task/openapi/upload"), body, {"Content-Type": kind},
                                    180, "RunningHub 上传")
            result = json.loads(content)
            name = (result.get("data") or {}).get("fileName")
            if str(result.get("code")) != "0" or not name:
                raise RuntimeError("RunningHub 参考音色上传失败：" + str(result.get("msg") or "未知错误"))
            index[digest] = name
            try:
                self.upload_index.parent.mkdir(parents=True, exist_ok=True)
                self.upload_index.write_text(json.dumps(index), encoding="utf-8")
            except OSError:
                pass
            return name

    def synthesize(self, text):
        key = runninghub_key()
        if not key:
            raise RuntimeError("未设置 RUNNINGHUB_API_KEY 环境变量")
        ref_name = self.reference_file_name(key)
        created = post_json(self.url("/task/openapi/create"), {
            "apiKey": key, "workflowId": self.config.workflow_id,
            "nodeInfoList": [
                {"nodeId": self.config.audio_node, "fieldName": self.config.audio_field, "fieldValue": ref_name},
                {"nodeId": self.config.text_node, "fieldName": self.config.text_field, "fieldValue": text},
            ]}, label="RunningHub")
        task_id = (created.get("data") or {}).get("taskId")
        if str(created.get("code")) != "0" or not task_id:
            raise RuntimeError("RunningHub 任务创建失败：" + str(created.get("msg") or "未知错误"))
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            status = post_json(self.url("/task/openapi/status"), {"apiKey": key, "taskId": task_id},
                               label="RunningHub")
            state = str(status.get("data") or "").upper()
            if state == "FAILED":
                raise RuntimeError("RunningHub 任务失败")
            if state not in ("QUEUED", "RUNNING"):
                # SUCCESS 或未知状态时直接取 outputs；任务未完成时 outputs 返回非 0 code（如 804）。
                outputs = post_json(self.url("/task/openapi/outputs"), {"apiKey": key, "taskId": task_id},
                                    label="RunningHub")
                items = outputs.get("data") if str(outputs.get("code")) == "0" else None
                files = [item.get("fileUrl") for item in (items if isinstance(items, list) else [])
                         if isinstance(item, dict) and item.get("fileUrl")]
                audio = [url for url in files if re.search(r"\.(flac|wav|mp3|ogg|m4a)(\?|$)", url)] or files
                if audio:
                    content, kind = http_bytes(audio[0], timeout=120, label="RunningHub 音频下载")
                    return content, audio_kind(content, kind)
                if state == "SUCCESS":
                    raise RuntimeError("RunningHub 任务没有返回音频")
            time.sleep(self.poll_interval)
        raise RuntimeError(f"RunningHub 任务超时（{self.timeout} 秒）")


def synthesize_local_indextts(config, text):
    """自建 IndexTTS HTTP 服务：POST {"text", "reference_audio"}，返回音频，或 JSON 中的 audio_base64 / audio_url。"""
    endpoint = config.local_endpoint
    checked_endpoint(endpoint)
    payload = {"text": text, "reference_audio": str(config.ref_audio) if config.ref_audio else ""}
    content, kind = http_bytes(endpoint, json.dumps(payload).encode("utf-8"),
                               {"Content-Type": "application/json"}, 300, "本地 IndexTTS")
    if kind == "application/json":
        value = json.loads(content)
        if value.get("audio_base64"):
            content = base64.b64decode(value["audio_base64"])
        elif value.get("audio_url"):
            content, kind = http_bytes(value["audio_url"], timeout=120, label="本地 IndexTTS")
        else:
            raise RuntimeError("本地 IndexTTS 没有返回音频：" + str(value.get("error") or ""))
    return content, audio_kind(content, kind)


def synthesize_openai(body, text):
    """OpenAI 兼容 /audio/speech，适用于大多数云端 TTS 服务商。"""
    checked_endpoint(body.get("endpoint"))
    headers = {"Content-Type": "application/json"}
    if body.get("key"):
        headers["Authorization"] = "Bearer " + str(body["key"])
    payload = {"model": body.get("model") or "tts-1", "input": text,
               "voice": body.get("voice") or "alloy", "response_format": "mp3"}
    content, kind = http_bytes(body["endpoint"], json.dumps(payload).encode("utf-8"), headers, 90, "TTS 服务")
    return content, audio_kind(content, kind)


def synthesize(config, body, cache=None, runninghub=None):
    """按 backend 合成一句话，返回 (音频字节, Content-Type)。browser/off 由网页自己处理。"""
    backend = str(body.get("backend") or "openai")
    text = str(body.get("text") or "").strip()[:1000]
    if not text:
        raise ValueError("朗读文本为空")
    if backend not in TTS_BACKENDS or backend in ("browser", "off"):
        raise ValueError("服务端不处理该 TTS 后端：" + backend)
    if backend == "openai":
        body = config.fill_service(body, "tts")
        voice_id = "|".join([body.get("endpoint", ""), str(body.get("model", "")), str(body.get("voice", ""))])
    elif backend == "runninghub":
        voice_id = "|".join([config.workflow_id, config.ref_file_name, str(config.ref_audio or "")])
    else:
        voice_id = "|".join([config.local_endpoint, str(config.ref_audio or "")])
    cache = cache or SpeechCache(config.cache_dir)
    key = cache.key(backend, voice_id, text)
    if body.get("cache", True):
        hit = cache.get(key)
        if hit:
            return hit
    if backend == "openai":
        result = synthesize_openai(body, text)
    elif backend == "runninghub":
        result = (runninghub or RunningHubIndexTTS(config)).synthesize(text)
    else:
        result = synthesize_local_indextts(config, text)
    cache.put(key, *result)
    return result


# ---------------------------------------------------------------- ASR

_whisper = {"model": None, "name": None}
_whisper_lock = threading.Lock()


def transcribe(config, body):
    """body: {backend, audio(base64), mime, endpoint, key, model, language}，返回 {"text", "backend"}。"""
    backend = str(body.get("backend") or config.asr_backend)
    try:
        audio = base64.b64decode(str(body.get("audio") or ""), validate=True)
    except ValueError as exc:
        raise ValueError("录音数据不是有效的 base64") from exc
    if not audio:
        raise ValueError("录音为空")
    mime = str(body.get("mime") or "audio/webm").split(";")[0]
    suffix = {"audio/wav": "wav", "audio/x-wav": "wav", "audio/ogg": "ogg", "audio/mpeg": "mp3",
              "audio/mp4": "m4a"}.get(mime, "webm")
    language = str(body.get("language") or config.asr["language"] or "")
    if backend == "openai":
        body = config.fill_service(body, "asr")
        checked_endpoint(body.get("endpoint"))
        fields = {"model": body.get("model") or "whisper-1", "response_format": "json"}
        if language:
            fields["language"] = language
        data, kind = multipart(fields, [("file", "speech." + suffix, mime, audio)])
        headers = {"Content-Type": kind}
        if body.get("key"):
            headers["Authorization"] = "Bearer " + str(body["key"])
        content, ctype = http_bytes(body["endpoint"], data, headers, 120, "语音识别服务")
        if ctype == "application/json":
            value = json.loads(content)
            text = value.get("text") if isinstance(value, dict) else ""
        else:
            text = content.decode("utf-8", "replace")
        return {"text": str(text or "").strip(), "backend": "openai"}
    if backend == "local":
        with _whisper_lock:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError("未安装 faster-whisper：请运行 pip install -r requirements-voice.txt") from exc
            name = str(body.get("model") or config.asr["model"] or "small")
            if _whisper["name"] != name:
                _whisper["model"] = WhisperModel(name, device="auto", compute_type="int8")
                _whisper["name"] = name
            with tempfile.NamedTemporaryFile(suffix="." + suffix, delete=False) as handle:
                handle.write(audio)
                path = handle.name
            try:
                # 中文提示词让 Whisper 倾向输出简体普通话。
                prompt = "以下是普通话的句子。" if language.startswith("zh") else None
                segments, _ = _whisper["model"].transcribe(path, language=language or None, vad_filter=True,
                                                           initial_prompt=prompt, condition_on_previous_text=False)
                text = "".join(segment.text for segment in segments)
            finally:
                os.unlink(path)
        return {"text": text.strip(), "backend": "local"}
    raise ValueError("浏览器识别在网页内完成，服务端只处理 openai / local")
