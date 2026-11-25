"""模拟 Confucius4-R2T2 ws_server.py 的 /asr_stream_api_v1 协议，用于在没有 GPU 时测试网页流式识别。

  pip install websockets
  python tests/mock_r2t2.py --port 8272 --text 我今天有点难过

协议与官方仓库一致：JSON 头 → 16kHz int16 PCM 二进制帧 → "YOUDAO_ONETIME_ASR_STREAM_EOS"；
每条结果的 msg.text 为新增片段（稳定前缀，不回改）。识别内容是固定文本，不是真实模型。
"""
import argparse
import asyncio
import json

import websockets

EOS = "YOUDAO_ONETIME_ASR_STREAM_EOS"


def make_handler(text, log):
    async def handle(ws):
        header = json.loads(await ws.recv())
        if header.get("secret_key") != "test0102":
            await ws.close(code=4401, reason="Unauthorized")
            return
        log.append({"header": header, "frames": []})
        await ws.send(json.dumps({"status": "connected", "requestId": header.get("requestId"), "msg": ""}))
        sent = 0
        async for data in ws:
            if isinstance(data, str):
                if data == EOS:
                    await ws.send(json.dumps({"status": "success", "msg": {"text": text[sent:], "reset": True}},
                                             ensure_ascii=False))
                    await ws.close()
                    item = log[-1]
                    print(json.dumps({"header": {k: v for k, v in item["header"].items() if k != "secret_key"},
                                      "frame_bytes": sorted(set(item["frames"])), "frames": len(item["frames"])},
                                     ensure_ascii=False), flush=True)
                    return
                continue
            log[-1]["frames"].append(len(data))
            # 每收到约 0.8 秒音频提交一个字：模拟稳定前缀逐步增长。
            if len(log[-1]["frames"]) % 5 == 0 and sent < len(text):
                await ws.send(json.dumps({"status": "success", "msg": {"text": text[sent], "reset": False}},
                                         ensure_ascii=False))
                sent += 1
            else:
                await ws.send(json.dumps({}))
    return handle


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8272)
    parser.add_argument("--text", default="我今天有点难过")
    args = parser.parse_args()
    log = []
    async with websockets.serve(make_handler(args.text, log), "127.0.0.1", args.port):
        print(f"Mock R2T2: ws://127.0.0.1:{args.port}/asr_stream_api_v1", flush=True)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
