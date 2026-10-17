# -*- coding: utf-8 -*-
"""只更新指定文件（Contents API），用于日常小改动，不用重传整个仓库。

用法：GH_TOKEN=xxx python upload_few.py <repo_dir> <file1> [file2 ...]
"""
import base64, json, os, sys, time, urllib.error, urllib.parse, urllib.request

TOKEN = os.environ.get("GH_TOKEN", "").strip()
OWNER, REPO = "corrinsh", "lottery-2026"
API, BRANCH = "https://api.github.com", "main"
BASE = sys.argv[1]
FILES = sys.argv[2:]
sys.stdout.reconfigure(encoding="utf-8")


def req(method, path, body=None, tries=3):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(API + path, data=data, method=method, headers={
                "Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json",
                "Content-Type": "application/json; charset=utf-8", "User-Agent": "corrin-lottery-upload"})
            with urllib.request.urlopen(r, timeout=90) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (401, 403, 404, 422):
                raise RuntimeError(f"HTTP {e.code} {method} {path}: {detail}")
            last = detail
        except Exception as e:
            last = str(e)
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"{method} {path}: {last}")


for f in FILES:
    url_path = urllib.parse.quote(f)
    raw = open(os.path.join(BASE, f), "rb").read()
    body = {"message": f"更新 {f}", "content": base64.b64encode(raw).decode(), "branch": BRANCH}
    try:
        cur = req("GET", f"/repos/{OWNER}/{REPO}/contents/{url_path}?ref={BRANCH}")
        body["sha"] = cur["sha"]
        res = req("PUT", f"/repos/{OWNER}/{REPO}/contents/{url_path}", body)
        print(f"  已更新 {f}  ({round(len(raw)/1024,1)} KB)  commit {res['commit']['sha'][:8]}")
    except RuntimeError as e:
        print(f"  失败 {f}: {e}")
print("== 完成 ==")
