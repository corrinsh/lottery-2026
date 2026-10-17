# -*- coding: utf-8 -*-
"""通过 GitHub Git Data API 上传整个目录（绕过 git push，因为 github.com 直连被重置）。

用法：GH_TOKEN=xxx python upload_api.py <repo_dir>
"""
import base64, json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

TOKEN = os.environ.get("GH_TOKEN", "").strip()
OWNER = "corrinsh"
REPO = "lottery-2026"
API = "https://api.github.com"
BASE = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
BRANCH = "main"

sys.stdout.reconfigure(encoding="utf-8")
if not TOKEN:
    raise SystemExit("缺少 GH_TOKEN")


def req(method, path, body=None, tries=3):
    url = API + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": "token " + TOKEN,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "corrin-lottery-upload",
            })
            with urllib.request.urlopen(r, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code in (401, 403, 404, 422):
                raise RuntimeError(f"HTTP {e.code} {method} {path}: {detail}")
            last = f"HTTP {e.code}: {detail}"
        except Exception as e:
            last = str(e)
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{method} {path} 失败: {last}")


def list_files():
    out = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files"],
        cwd=BASE).decode("utf-8")
    return [p for p in out.splitlines() if p.strip()]


def main():
    files = list_files()
    print(f"待上传 {len(files)} 个文件")
    total = sum(os.path.getsize(os.path.join(BASE, f)) for f in files)
    print(f"合计 {round(total/1024/1024, 2)} MB")

    # 1) 用 README.md 建初始 commit（新仓库没有 main 分支）
    readme = os.path.join(BASE, "README.md")
    content = base64.b64encode(open(readme, "rb").read()).decode()
    body = {"message": "初始化仓库", "content": content, "branch": BRANCH}
    try:
        r = req("PUT", f"/repos/{OWNER}/{REPO}/contents/README.md", body)
    except RuntimeError as e:
        if "HTTP 422" in str(e):
            cur = req("GET", f"/repos/{OWNER}/{REPO}/contents/README.md?ref={BRANCH}")
            body["sha"] = cur["sha"]
            r = req("PUT", f"/repos/{OWNER}/{REPO}/contents/README.md", body)
        else:
            raise
    base_commit = r["commit"]["sha"]
    print(f"初始 commit: {base_commit[:8]}")

    commit_info = req("GET", f"/repos/{OWNER}/{REPO}/git/commits/{base_commit}")
    base_tree = commit_info["tree"]["sha"]

    # 2) 逐个上传 blob
    tree = []
    for i, path in enumerate(files, 1):
        if path == "README.md":
            continue
        full = os.path.join(BASE, path)
        raw = open(full, "rb").read()
        b64 = base64.b64encode(raw).decode()
        blob = req("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
                   {"content": b64, "encoding": "base64"})
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  [{i}/{len(files)}] {path}  {round(len(raw)/1024, 1)} KB")

    if not tree:
        print("没有需要上传的文件")
        return

    # 3) 建 tree + commit + 移动分支
    new_tree = req("POST", f"/repos/{OWNER}/{REPO}/git/trees",
                   {"base_tree": base_tree, "tree": tree})
    new_commit = req("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
        "message": "上传 2026 年大乐透 / 双色球开奖数据与交互看板",
        "tree": new_tree["sha"],
        "parents": [base_commit],
    })
    req("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", {"sha": new_commit["sha"]})
    print(f"== 完成 == commit {new_commit['sha'][:8]}，{len(tree)+1} 个文件")


if __name__ == "__main__":
    main()
