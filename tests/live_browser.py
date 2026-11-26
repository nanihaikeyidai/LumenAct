"""Exercise the local live page and record its actual canvas and playback audio."""
import argparse
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument("--url",default="http://127.0.0.1:8794/preview/live.html")
parser.add_argument("--out",type=Path,required=True)
args=parser.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as api:
    browser=api.chromium.launch(channel="chromium",args=["--autoplay-policy=no-user-gesture-required","--enable-unsafe-swiftshader"])
    page=browser.new_page(viewport={"width":960,"height":700})
    errors=[]
    page.on("pageerror",lambda err:errors.append(str(err)))
    page.add_init_script("""window.NativeAudio=AudioContext;window.AudioContext=class extends NativeAudio {
        constructor(){super();window.mix=this.createMediaStreamDestination();}
        createAnalyser(){const a=super.createAnalyser();a.connect(window.mix);window.meter=a;return a;}
    };""")
    page.goto(args.url)
    page.wait_for_function("!document.querySelector('#play').disabled",timeout=60000)
    page.locator("canvas").screenshot(path=str(args.out/"idle.png"))
    lines=["（挥手，微笑）大家好，欢迎来到今天的直播。","（点头，眨眼）没错，请看这里。","（讲解，挑眉）真的吗？谢谢大家，再见。","（摇头）没错，请看这里。"]
    for i,line in enumerate(lines):
        page.locator("input").fill(line)
        page.locator("#play").click()
        if i==0:
            page.evaluate("""() => {
              const video=document.querySelector('canvas').captureStream(24);
              video.addTrack(window.mix.stream.getAudioTracks()[0]);
              window.chunks=[];window.rec=new MediaRecorder(video,{mimeType:'video/webm;codecs=vp8,opus'});
              rec.ondataavailable=e=>chunks.push(e.data);rec.start();
            }""")
    observed=[]
    for i,line in enumerate(lines):
        text=line.split("）")[1]
        page.wait_for_function("s=>document.querySelector('#status').textContent===s",arg=text,timeout=180000)
        page.wait_for_timeout(400)
        observed.append(page.evaluate("""()=>{let buf=new Float32Array(meter.fftSize);meter.getFloatTimeDomainData(buf);return Math.max(...buf.map(Math.abs));}"""))
        page.locator("canvas").screenshot(path=str(args.out/f"cue-{i}.png"))
    page.wait_for_function("document.querySelector('#status').textContent==='播报结束'",timeout=30000)
    payload=page.evaluate("""() => new Promise(resolve=>{rec.onstop=()=>{const r=new FileReader();
      r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(new Blob(chunks));};rec.stop();})""")
    (args.out/"live.webm").write_bytes(base64.b64decode(payload))
    page.locator("input").fill(lines[0]);page.locator("#play").click()
    page.wait_for_function("document.querySelector('#status').textContent.includes('大家好')")
    page.locator("#stop").click()
    assert page.locator("#status").inner_text()=="已停止"
    assert not errors,errors
    assert max(observed)>.01,observed
    print(json.dumps({"peak_samples":observed,"played":len(lines),"stop":"passed","page_errors":errors}))
    browser.close()
