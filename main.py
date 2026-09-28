import importlib.util
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

spec = importlib.util.spec_from_file_location(
    "translator", os.path.join(os.path.dirname(__file__), "translator.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ROWS = m.load_dict()

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI翻译 - 在线翻译</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 16px;
  }
  .container {
    width: 100%;
    max-width: 720px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    padding: 32px;
  }
  h1 {
    font-size: 24px;
    color: #1f2d3d;
    margin-bottom: 6px;
  }
  .subtitle {
    font-size: 13px;
    color: #8492a6;
    margin-bottom: 24px;
  }
  label {
    display: block;
    font-size: 14px;
    color: #475669;
    margin-bottom: 8px;
  }
  textarea {
    width: 100%;
    min-height: 140px;
    padding: 12px 14px;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    font-size: 15px;
    line-height: 1.6;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }
  textarea:focus { border-color: #409eff; }
  .rand-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 20px;
    margin-bottom: 20px;
  }
  input[type="range"] { flex: 1; accent-color: #409eff; }
  .rand-value {
    font-size: 14px;
    color: #1f2d3d;
    background: #f0f2f5;
    border-radius: 6px;
    padding: 4px 10px;
    min-width: 52px;
    text-align: center;
  }
  .btn {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 8px;
    background: #409eff;
    color: #fff;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .btn:hover { background: #66b1ff; }
  .btn:active { background: #3a8ee6; }
  .btn:disabled { background: #a0cfff; cursor: not-allowed; }
  .result {
    margin-top: 24px;
  }
  .result-title {
    font-size: 14px;
    color: #8492a6;
    margin-bottom: 8px;
  }
  #output {
    min-height: 60px;
    padding: 14px;
    background: #f8fafc;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    font-size: 16px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-all;
    color: #1f2d3d;
  }
  .error {
    background: #fef0f0 !important;
    border-color: #f56c6c !important;
    color: #f56c6c !important;
  }
  .note {
    margin-top: 20px;
    font-size: 12px;
    color: #c0c4cc;
    line-height: 1.8;
  }
</style>
</head>
<body>
<div class="container">
  <h1>AI翻译</h1>
  <p class="subtitle">English → 中文 翻译工具</p>

  <label for="source">原文 (English)</label>
  <textarea id="source" placeholder="输入要翻译的英文文本，例如：Good morning"></textarea>

  <div class="rand-row">
    <label for="rand" style="margin:0; white-space:nowrap;">随机度</label>
    <input type="range" id="rand" min="0" max="1" step="0.005" value="0.5">
    <span class="rand-value" id="randValue">0.500</span>
  </div>

  <button class="btn" id="btn">翻译</button>

  <div class="result">
    <div class="result-title">译文</div>
    <div id="output">等待输入…</div>
  </div>

  <p class="note">
    说明：随机度 0 时恒取每个词的第一个释义，随机度 1 时所有释义等概率抽取。
    rand 值越大，翻译结果越随机。数字原样保留，逗号句号自动转换为中文标点。
  </p>
</div>

<script>
  const source = document.getElementById("source");
  const randInput = document.getElementById("rand");
  const randValue = document.getElementById("randValue");
  const btn = document.getElementById("btn");
  const output = document.getElementById("output");

  randInput.addEventListener("input", function () {
    randValue.textContent = parseFloat(this.value).toFixed(3);
  });

  source.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") translate();
  });

  btn.addEventListener("click", translate);

  async function translate() {
    const text = source.value.trim();
    if (!text) return;
    btn.disabled = true;
    btn.textContent = "翻译中…";
    output.classList.remove("error");
    try {
      const resp = await fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rand: parseFloat(randInput.value), data: text })
      });
      const result = await resp.json();
      if (result.error) {
        output.textContent = result.error;
        output.classList.add("error");
      } else {
        output.textContent = result.answer;
      }
    } catch (err) {
      output.textContent = "请求失败：" + err.message;
      output.classList.add("error");
    } finally {
      btn.disabled = false;
      btn.textContent = "翻译";
    }
  }
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            req = json.loads(body.decode("utf-8"))
            data = str(req.get("data", ""))
            rand = float(req.get("rand", 0.5))
            rand = min(1.0, max(0.0, rand))
            answer = m.translate(data, ROWS, rand)
            self.send_json({"answer": answer})
        except Exception:
            self.send_json({"error": "invalid request, expect {\"rand\":0.5,\"data\":\"Good\"}"}, 400)

    def do_GET(self):
        payload = INDEX_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, obj, code=200):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = 8080
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("机翻服务已启动: http://127.0.0.1:%d" % port)
    server.serve_forever()
