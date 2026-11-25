"""可选：把本机 IndexTTS 包装成 LumenAct 的「IndexTTS 本地 / 自建 HTTP」TTS 后端。

接口约定（voice_services.synthesize_local_indextts）：
  POST /tts  {"text": "...", "reference_audio": "/path/ref.wav"}  →  audio/wav

依赖官方 index-tts 仓库（https://github.com/index-tts/index-tts）的 IndexTTS2 Python 接口，
需按其 README 安装并下载 checkpoints；通常需要 NVIDIA GPU。本脚本未在 LumenAct 的测试环境中实机运行。

  python tools/indextts_http_server.py --model-dir /path/to/index-tts/checkpoints --port 9880
  LUMENACT_INDEXTTS_ENDPOINT=http://127.0.0.1:9880/tts python server.py
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading


def main():
    parser = argparse.ArgumentParser(description="IndexTTS → HTTP 适配")
    parser.add_argument("--model-dir", required=True, help="index-tts 的 checkpoints 目录")
    parser.add_argument("--reference", help="默认参考音色 wav（请求未提供 reference_audio 时使用）")
    parser.add_argument("--port", type=int, default=9880)
    parser.add_argument("--fp16", action="store_true")
    args = parser.parse_args()
    from indextts.infer_v2 import IndexTTS2  # 官方 IndexTTS2 接口
    model_dir = Path(args.model_dir)
    tts = IndexTTS2(cfg_path=str(model_dir / "config.yaml"), model_dir=str(model_dir), use_fp16=args.fp16)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                text = str(body.get("text") or "").strip()
                reference = body.get("reference_audio") or args.reference
                if not text or not reference or not Path(reference).is_file():
                    raise ValueError("需要 text 与存在的 reference_audio")
                with tempfile.TemporaryDirectory() as directory, lock:
                    output = Path(directory) / "out.wav"
                    tts.infer(spk_audio_prompt=str(reference), text=text, output_path=str(output))
                    content = output.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
            except Exception as exc:  # 返回 JSON 错误，LumenAct 会显示并回退浏览器朗读
                content = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    print(f"IndexTTS HTTP: http://127.0.0.1:{args.port}/tts", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
