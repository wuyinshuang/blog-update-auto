"""
MCP Server: Blog Auto-Updater
Exposes a tool that Trae IDE (or any MCP client) can call to update the blog.

How to install dependencies:
    pip install mcp

How to run (stdio mode, for MCP factory):
    python mcp_blog_updater.py

How to test standalone:
    python -c "from mcp_blog_updater import update_blog_sync; print(update_blog_sync())"
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import urllib.error
import json
import time
from typing import List, Dict

# ---------- config ----------
GIT_DIR = r"D:\github_page\wuyinshuang.github.io"
GITHUB_REPO_URL = "https://github.com/wuyinshuang/wuyinshuang.github.io"
GIT_COMMIT_MSG = "update blog"


# ---------- core logic (sync, returns structured result) ----------

def copy_images() -> List[Dict[str, str]]:
    """Copy _posts/images -> images, skip duplicates. Return file ops."""
    src = os.path.join(GIT_DIR, "_posts", "images")
    dst = os.path.join(GIT_DIR, "images")
    ops: List[Dict[str, str]] = []

    if not os.path.isdir(src):
        return [{"status": "warning", "message": "_posts/images 目录不存在，已跳过"}]

    os.makedirs(dst, exist_ok=True)

    for fname in os.listdir(src):
        sf = os.path.join(src, fname)
        df = os.path.join(dst, fname)
        if not os.path.isfile(sf):
            continue
        if os.path.exists(df):
            ops.append({"status": "skipped", "file": fname, "message": "已存在，跳过"})
            continue
        shutil.copy2(sf, df)
        ops.append({"status": "copied", "file": fname, "message": "复制成功"})

    return ops


def run_git_cmd(cmd: str) -> Dict:
    """Run a git command, return {returncode, stdout, stderr}."""
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=GIT_DIR,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = proc.communicate()
        return {
            "returncode": proc.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
        }
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def check_github_push() -> Dict:
    """Verify the latest push via GitHub API."""
    api_url = "https://api.github.com/repos/wuyinshuang/wuyinshuang.github.io/commits"

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "blog-updater-mcp",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data:
                        c = data[0]
                        return {
                            "verified": True,
                            "latest_commit": {
                                "sha": c["sha"][:7],
                                "message": c["commit"]["message"],
                                "author": c["commit"]["author"]["name"],
                                "date": c["commit"]["author"]["date"],
                            },
                        }
                    return {"verified": True, "latest_commit": None}
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < 2:
                time.sleep(3 ** (attempt + 1))
                continue
            return {"verified": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            if attempt < 2:
                time.sleep(3 ** (attempt + 1))
                continue
            return {"verified": False, "error": str(e)}

    return {"verified": False, "error": "API 重试耗尽"}


def update_blog_sync() -> Dict:
    """
    Execute the full blog update pipeline.
    Returns a structured dict with all steps and results.
    """
    result: Dict = {
        "success": False,
        "steps": [],
        "github_check": None,
    }

    # Step 0: copy images
    image_ops = copy_images()
    copied_count = sum(1 for o in image_ops if o["status"] == "copied")
    skipped_count = sum(1 for o in image_ops if o["status"] == "skipped")
    result["steps"].append({
        "step": "复制图片",
        "command": f"copy _posts/images -> images",
        "details": image_ops,
        "summary": f"复制 {copied_count} 个，跳过 {skipped_count} 个",
        "success": True,
    })

    # Step 1: git add .
    r1 = run_git_cmd("git add .")
    step1: Dict = {
        "step": "git add",
        "command": "git add .",
        "stdout": r1["stdout"],
        "stderr": r1["stderr"],
        "success": r1["returncode"] == 0,
    }
    result["steps"].append(step1)
    if not step1["success"]:
        result["error"] = f"git add 失败: {r1['stderr']}"
        return result

    # Step 2: git commit
    r2 = run_git_cmd(f'git commit -m "{GIT_COMMIT_MSG}"')
    step2: Dict = {
        "step": "git commit",
        "command": f'git commit -m "{GIT_COMMIT_MSG}"',
        "stdout": r2["stdout"],
        "stderr": r2["stderr"],
        "success": r2["returncode"] == 0,
    }
    result["steps"].append(step2)
    # non-zero is ok if nothing to commit
    if r2["returncode"] != 0 and "nothing to commit" not in r2["stdout"] + r2["stderr"]:
        result["error"] = f"git commit 失败: {r2['stderr']}"
        return result

    # Step 3: git push
    r3 = run_git_cmd("git push")
    step3: Dict = {
        "step": "git push",
        "command": "git push",
        "stdout": r3["stdout"],
        "stderr": r3["stderr"],
        "success": r3["returncode"] == 0,
    }
    result["steps"].append(step3)
    if not step3["success"]:
        result["error"] = f"git push 失败: {r3['stderr']}"
        return result

    # Step 4: verify on GitHub
    gh = check_github_push()
    result["github_check"] = gh
    result["success"] = gh.get("verified", False)

    return result


# ---------- MCP server ----------

def serve_mcp():
    """Run the MCP server over stdio (compatible with MCP factory / stdio transport)."""
    try:
        from mcp.server import Server, NotificationOptions
        from mcp.server.models import InitializationOptions
        import mcp.server.stdio
        import mcp.types as types
    except ImportError:
        print('需要安装 mcp 包: pip install mcp', file=sys.stderr)
        sys.exit(1)

    server = Server("blog-updater")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="update_blog",
                description="更新 GitHub Pages 博客：复制图片 -> git add -> git commit -> git push -> 验证",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        if name != "update_blog":
            raise ValueError(f"未知工具: {name}")

        result = update_blog_sync()

        lines = []
        for step in result["steps"]:
            lines.append(f"## {step['step']}")
            lines.append(f"  $ {step['command']}")

            details = step.get("details")
            if details:
                for d in details:
                    icon = {"copied": "✅", "skipped": "⏭️", "warning": "⚠️"}.get(d["status"], "")
                    lines.append(f"  {icon} {d.get('file', '')} {d['message']}")

            if step.get("summary"):
                lines.append(f"  {step['summary']}")

            std = step.get("stdout")
            if std:
                for line in std.split("\n"):
                    lines.append(f"  {line}")
            stde = step.get("stderr")
            if stde:
                for line in stde.split("\n"):
                    lines.append(f"  {line}")

            status = "✅ 成功" if step["success"] else "❌ 失败"
            lines.append(f"  状态: {status}")
            lines.append("")

        gh = result.get("github_check")
        if gh:
            lines.append("## GitHub 验证")
            if gh.get("verified"):
                lc = gh.get("latest_commit")
                if lc:
                    lines.append(f"  ✅ 验证成功！最新提交: {lc['sha']} - {lc['message']}")
                else:
                    lines.append("  ✅ 验证成功")
            else:
                lines.append(f"  ⚠️ 验证失败: {gh.get('error', '未知错误')}")

        if result["success"]:
            lines.append("🎉 博客更新全部完成！")
        else:
            lines.append(f"❌ 博客更新失败: {result.get('error', '未知错误')}")

        return [types.TextContent(type="text", text="\n".join(lines))]

    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="blog-updater",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    import asyncio
    asyncio.run(run())


# ---------- entry ----------

if __name__ == "__main__":
    serve_mcp()
