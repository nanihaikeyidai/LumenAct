"""Local Tripo live stage backed by ComfyUI IndexTTS 2.5."""
import argparse
import hashlib
import json
import threading
import time
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]


class Studio:
    def __init__(self, comfy, reference):
        self.url = comfy.rstrip("/")
        self.reference = reference
        self.lock = threading.Lock()

    @lru_cache(maxsize=1)
    def setup(self):
        nodes = {}
        for name in ("T8_IndexTTS25_ModelLoader", "T8_IndexTTS25_Generate"):
            response = requests.get(f"{self.url}/object_info/{name}", timeout=30)
            response.raise_for_status()
            required = response.json()[name]["input"]["required"]
            nodes[name] = {key: spec[1]["default"] for key, spec in required.items()
                           if len(spec)>1 and "default" in spec[1]}
        content = self.reference.read_bytes()
        name = "live-ref-" + hashlib.sha256(content).hexdigest()[:20] + ".wav"
        response = requests.post(self.url+"/upload/image", files={"image":(name,content,"audio/wav")},timeout=60)
        response.raise_for_status()
        return nodes, response.json()["name"]

    @lru_cache(maxsize=32)
    def speech(self, text):
        nodes, reference = self.setup()
        loader, generate = nodes
        graph = {
            "1":{"class_type":loader,"inputs":nodes[loader]},
            "2":{"class_type":"LoadAudio","inputs":{"audio":reference}},
            "3":{"class_type":generate,"inputs":dict(nodes[generate],model=["1",0],
                  speaker_audio=["2",0],text=text,language="ZH",seed=2026)},
            "4":{"class_type":"SaveAudio","inputs":{"audio":["3",0],"filename_prefix":"LumenLive/voice"}}
        }
        response = requests.post(self.url+"/prompt",json={"prompt":graph},timeout=30)
        if not response.ok:
            raise RuntimeError(response.text[:1000])
        job = response.json()["prompt_id"]
        deadline = time.monotonic()+600
        while time.monotonic()<deadline:
            result=requests.get(self.url+"/history/"+job,timeout=20).json().get(job)
            if result:
                files=result.get("outputs",{}).get("4",{}).get("audio",[])
                if not files:
                    raise RuntimeError("ComfyUI synthesis failed: "+str(result.get("status",{}))[-900:])
                audio=requests.get(self.url+"/view",params=files[0],timeout=60)
                audio.raise_for_status()
                return audio.content
            time.sleep(.4)
        raise TimeoutError("IndexTTS 等待超时")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reference",required=True,type=Path)
    parser.add_argument("--comfy",default="http://127.0.0.1:8188")
    parser.add_argument("--port",type=int,default=8794)
    args=parser.parse_args()
    if not args.reference.is_file():
        parser.error("参考音频不存在")
    studio=Studio(args.comfy,args.reference)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,directory=str(ROOT),**kwargs)

        def do_GET(self):
            if self.path=="/":
                self.send_response(302)
                self.send_header("Location","/preview/live.html")
                self.end_headers()
            else:
                super().do_GET()

        def do_POST(self):
            if self.path!="/api/live/speech":
                return self.send_error(404)
            origin=self.headers.get("Origin")
            if origin and urlsplit(origin).netloc!=self.headers.get("Host"):
                return self.send_error(403)
            try:
                length=int(self.headers.get("Content-Length",0))
                if not 0<length<=8192:
                    return self.send_error(400)
                text=json.loads(self.rfile.read(length))["text"]
                if not isinstance(text,str) or not 0<len(text.strip())<=500:
                    return self.send_error(400)
                with studio.lock:
                    audio=studio.speech(text.strip())
                self.send_response(200)
                self.send_header("Content-Type","audio/flac")
                self.send_header("Content-Length",str(len(audio)))
                self.end_headers()
                self.wfile.write(audio)
            except (BrokenPipeError,ConnectionResetError):
                pass
            except Exception as error:
                self.send_error(503,str(error).encode("ascii","backslashreplace").decode()[:400])

    ThreadingHTTPServer(("127.0.0.1",args.port),Handler).serve_forever()


if __name__=="__main__":
    main()
