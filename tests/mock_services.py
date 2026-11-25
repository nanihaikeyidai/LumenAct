"""本地模拟服务：不需要任何密钥即可演示 / 测试语音对话链路。

  python tests/mock_services.py --port 9100

提供 OpenAI 兼容的 /v1/chat/completions、/v1/audio/speech、/v1/audio/transcriptions，
RunningHub 的 /task/openapi/{upload,create,status,outputs}（返回生成的 wav），
以及自建 IndexTTS 接口 /indextts。仅用于开发测试，回复内容是固定规则，不是真实模型。
"""
import argparse
import io
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import struct
import threading
from urllib.parse import urlsplit
import wave

RULES = [("难过", "(担忧担心)别难过，我在这里陪着你。"), ("开心", "(开心欢快)太好了！听到你开心我也很开心！"),
         ("生气", "(道歉抱歉)对不起，是我没做好，我们慢慢说。"), ("厉害", "(骄傲自豪)那当然，交给我就对了！"),
         ("无标签", "哇，你竟然真的做到了？太厉害了！"), ("json", '{"expression": "星星眼", "text": "好期待呀！"}')]


def tone_wav(text, rate=16000):
    """按字数生成带音节起伏的提示音，便于测试口型包络与字幕进度。"""
    seconds = max(.6, len(text) * .18)
    frames = bytearray()
    for i in range(int(seconds * rate)):
        t = i / rate
        envelope = .5 + .5 * math.sin(2 * math.pi * 4.5 * t)
        frames += struct.pack("<h", int(9000 * envelope * math.sin(2 * math.pi * 220 * t)))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1); handle.setsampwidth(2); handle.setframerate(rate); handle.writeframes(bytes(frames))
    return buffer.getvalue()


class State:
    def __init__(self):
        self.requests = []
        self.tasks = {}
        self.lock = threading.Lock()


def handler(state):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, kind="application/json"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path.startswith("/files/"):
                text = state.tasks.get(path.rsplit("/", 1)[-1].split(".")[0], "你好")
                self.send(200, tone_wav(text), "audio/wav")
            else:
                self.send(404, {"error": "not found"})

        def do_POST(self):
            path = urlsplit(self.path).path
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            kind = self.headers.get("Content-Type", "")
            body = json.loads(raw) if kind.startswith("application/json") and raw else {}
            with state.lock:
                state.requests.append({"path": path, "headers": dict(self.headers), "body": body, "raw": raw})
            if path.endswith("/chat/completions"):
                user = next((m["content"] for m in reversed(body.get("messages", [])) if m.get("role") == "user"), "")
                reply = next((answer for key, answer in RULES if key in user), "(微笑)嗯嗯，我在听，你继续说。")
                self.send(200, {"choices": [{"message": {"role": "assistant", "content": reply}}]})
            elif path.endswith("/audio/speech"):
                self.send(200, tone_wav(body.get("input", "")), "audio/wav")
            elif path.endswith("/audio/transcriptions"):
                self.send(200, {"text": "我今天有点难过"})
            elif path == "/indextts":
                self.send(200, tone_wav(body.get("text", "")), "audio/wav")
            elif path == "/task/openapi/upload":
                self.send(200, {"code": 0, "msg": "success", "data": {"fileName": "api/mock-ref.wav", "fileType": "audio"}})
            elif path == "/task/openapi/create":
                text = next((item["fieldValue"] for item in body.get("nodeInfoList", []) if item.get("fieldName") == "prompt"), "")
                with state.lock:
                    task_id = str(1000 + len(state.tasks))
                    state.tasks[task_id] = text
                self.send(200, {"code": 0, "msg": "success", "data": {"taskId": task_id, "taskStatus": "QUEUED"}})
            elif path == "/task/openapi/status":
                self.send(200, {"code": 0, "msg": "success", "data": "SUCCESS"})
            elif path == "/task/openapi/outputs":
                host = self.headers.get("Host")
                self.send(200, {"code": 0, "msg": "success", "data": [
                    {"fileUrl": f"http://{host}/files/{body.get('taskId')}.wav", "fileType": "wav", "nodeId": "48"}]})
            else:
                self.send(404, {"error": "not found"})

        def log_message(self, *args):
            pass
    return Handler


def start(port=0):
    state = State()
    server = ThreadingHTTPServer(("127.0.0.1", port), handler(state))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LumenAct 语音对话模拟服务")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args()
    server, _ = start(args.port)
    base = f"http://127.0.0.1:{args.port}"
    print("Mock LLM :", base + "/v1/chat/completions")
    print("Mock TTS :", base + "/v1/audio/speech")
    print("Mock ASR :", base + "/v1/audio/transcriptions")
    print("Mock RunningHub base:", base, "（设置 LUMENACT_RH_BASE）", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.shutdown()
