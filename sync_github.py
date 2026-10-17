# -*- coding: utf-8 -*-
"""把本地仓库同步到 GitHub（走 API，因为 github.com 直连被重置）。

只上传 blob sha 与远程不同的文件，没变化的直接跳过。
Token 读取顺序：环境变量 GH_TOKEN → ~/.workbuddy/secrets/github_token.txt
"""
import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

OWNER, REPO = "corrinsh", "lottery-2026"
API, BRANCH = "https://api.github.com", "main"
BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "secrets", "github_token.txt")

sys.stdout.reconfigure(encoding="utf-8")


def token():
    t = os.environ.get("GH_TOKEN", "").strip()
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE, encoding="utf-8").read().strip()
    return t


TOKEN = token()
if not TOKEN:
    print("  跳过同步：未找到 GitHub token")
    raise SystemExit(0)


def req(method, path, body=None, tries=3):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(API + path, data=data, method=method, headers={
                "Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json",
                "Content-Type": "application/json; charset=utf-8", "User-Agent": "corrin-lottery-sync"})
            with urllib.request.urlopen(r, timeout=90) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 404:
                return None
            if e.code in (401, 403):
                raise RuntimeError(f"认证失败（token 可能已过期）: {detail}")
            last = f"HTTP {e.code}: {detail}"
        except Exception as e:
            last = str(e)
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"{method} {path}: {last}")


def local_files():
    out = subprocess.check_output(["git", "-c", "core.quotepath=false", "ls-files"],
                                  cwd=BASE).decode("utf-8")
    return [p for p in out.splitlines() if p.strip()]


def blob_sha(path):
    # 必须按原始字节算：git hash-object 会按 .gitattributes 做 eol 转换，与远端存的字节不一致
    import hashlib
    data = open(os.path.join(BASE, path), "rb").read()
    header = ("blob %d" % len(data)).encode() + bytes([0])
    return hashlib.sha1(header + data).hexdigest()


def main():
    files = local_files()
    changed, failed = [], []
    for f in files:
        remote = req("GET", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(f)}?ref={BRANCH}")
        if remote is None:
            changed.append((f, None))
            continue
        if remote.get("sha") != blob_sha(f):
            changed.append((f, remote["sha"]))

    if not changed:
        print(f"  GitHub 已是最新（{len(files)} 个文件均一致）")
        return

    print(f"  需要同步 {len(changed)} 个文件")
    for f, sha in changed:
        import base64
        raw = open(os.path.join(BASE, f), "rb").read()
        body = {"message": f"数据更新：{f}", "content": base64.b64encode(raw).decode(), "branch": BRANCH}
        if sha:
            body["sha"] = sha
        try:
            req("PUT", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(f)}", body)
            print(f"    ✓ {f}  {round(len(raw)/1024, 1)} KB")
        except Exception as e:
            print(f"    ✗ {f}: {e}")
            failed.append(f)

    if failed:
        print(f"  == 同步完成，{len(failed)} 个文件失败 ==")
        raise SystemExit(1)
    print(f"  == GitHub 同步完成（{len(changed)} 个文件）==")


if __name__ == "__main__":
    main()
