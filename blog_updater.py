import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import time
import os
import sys
import shutil
import urllib.request
import urllib.error

GIT_DIR = r"D:\github_page\wuyinshuang.github.io"
GITHUB_REPO_URL = "https://github.com/wuyinshuang/wuyinshuang.github.io"


def copy_images(text_widget):
    """Copy _posts/images to images, skip duplicates."""
    src_dir = os.path.join(GIT_DIR, "_posts", "images")
    dst_dir = os.path.join(GIT_DIR, "images")

    text_widget.insert(tk.END, f"> 复制图片: {src_dir} -> {dst_dir}\n", "command")
    text_widget.see(tk.END)

    if not os.path.isdir(src_dir):
        text_widget.insert(tk.END, f"  _posts/images 目录不存在，跳过。\n", "warning")
        text_widget.see(tk.END)
        return

    os.makedirs(dst_dir, exist_ok=True)

    copied = 0
    skipped = 0
    for fname in os.listdir(src_dir):
        src_file = os.path.join(src_dir, fname)
        dst_file = os.path.join(dst_dir, fname)
        if not os.path.isfile(src_file):
            continue
        if os.path.exists(dst_file):
            text_widget.insert(tk.END, f"  跳过 (已存在): {fname}\n", "warning")
            skipped += 1
            continue
        shutil.copy2(src_file, dst_file)
        text_widget.insert(tk.END, f"  复制: {fname}\n", "output")
        copied += 1

    text_widget.insert(
        tk.END, f"  完成: 复制 {copied} 个文件，跳过 {skipped} 个文件\n", "success"
    )
    text_widget.see(tk.END)


def run_command(cmd, cwd, text_widget, tag):
    """Run a shell command and stream output to the text widget."""
    text_widget.insert(tk.END, f"> {cmd}\n", "command")
    text_widget.see(tk.END)

    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
        )

        output_lines = []
        for line in iter(process.stdout.readline, ""):
            if line:
                text_widget.insert(tk.END, line, tag)
                text_widget.see(tk.END)
                output_lines.append(line)

        process.stdout.close()
        return_code = process.wait()
        return return_code, "".join(output_lines)
    except Exception as e:
        text_widget.insert(tk.END, f"Error: {e}\n", "error")
        text_widget.see(tk.END)
        return -1, str(e)


def check_github_push(text_widget):
    """Check GitHub to verify the latest push."""
    text_widget.insert(tk.END, "\n" + "=" * 50 + "\n", "separator")
    text_widget.insert(tk.END, "正在检查 GitHub 远程仓库状态...\n", "info")
    text_widget.see(tk.END)

    api_url = "https://api.github.com/repos/wuyinshuang/wuyinshuang.github.io/commits"

    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read().decode("utf-8")
                    import json

                    commits = json.loads(data)
                    if commits:
                        latest = commits[0]
                        sha = latest["sha"][:7]
                        msg = latest["commit"]["message"]
                        author = latest["commit"]["author"]["name"]
                        date = latest["commit"]["author"]["date"]
                        text_widget.insert(
                            tk.END,
                            f"\n最新提交:\n"
                            f"  SHA: {sha}\n"
                            f"  作者: {author}\n"
                            f"  时间: {date}\n"
                            f"  消息: {msg}\n",
                            "success",
                        )
                    text_widget.insert(
                        tk.END,
                        "\n✅ GitHub 推送验证成功！远程仓库已更新。\n",
                        "success",
                    )
                    return True
            break
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < retries - 1:
                text_widget.insert(
                    tk.END, f"API 限流，{3 ** (attempt + 1)} 秒后重试...\n", "warning"
                )
                time.sleep(3 ** (attempt + 1))
                continue
            text_widget.insert(
                tk.END,
                f"\n无法通过 API 验证 (HTTP {e.code})，将直接打开网页。\n",
                "warning",
            )
            break
        except Exception as e:
            if attempt < retries - 1:
                text_widget.insert(
                    tk.END,
                    f"API 访问失败 ({e})，{3 ** (attempt + 1)} 秒后重试...\n",
                    "warning",
                )
                time.sleep(3 ** (attempt + 1))
                continue
            text_widget.insert(tk.END, f"\nAPI 访问失败: {e}\n", "error")
            break

    # Fallback: open the web page
    import webbrowser

    text_widget.insert(tk.END, f"正在打开网页: {GITHUB_REPO_URL}\n", "info")
    webbrowser.open(GITHUB_REPO_URL)
    text_widget.insert(tk.END, "请手动确认网页是否正常显示最新提交。\n", "info")
    return False


def update_blog(btn, text_widget):
    """Main update flow, runs in a background thread."""
    btn.config(state=tk.DISABLED, text="正在更新...")
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "🚀 开始更新博客...\n\n", "title")
    text_widget.see(tk.END)

    # 0) Copy images from _posts/images to images
    copy_images(text_widget)
    text_widget.insert(tk.END, "\n", "")
    text_widget.see(tk.END)

    # 1) git add .
    rc1, _ = run_command("git add .", GIT_DIR, text_widget, "output")
    if rc1 != 0:
        text_widget.insert(tk.END, "\n❌ git add 失败，终止操作。\n", "error")
        btn.config(state=tk.NORMAL, text="自动更新博客")
        return

    # 2) git commit
    rc2, _ = run_command('git commit -m "update blog"', GIT_DIR, text_widget, "output")
    if rc2 != 0:
        # If nothing to commit, still ok
        text_widget.insert(
            tk.END, "\n⚠️  没有新的更改需要提交，继续推送...\n", "warning"
        )

    # 3) git push
    rc3, _ = run_command("git push", GIT_DIR, text_widget, "output")
    if rc3 != 0:
        text_widget.insert(tk.END, "\n❌ git push 失败，终止操作。\n", "error")
        btn.config(state=tk.NORMAL, text="自动更新博客")
        return

    # All done
    text_widget.insert(tk.END, "\n" + "=" * 50 + "\n", "separator")
    text_widget.insert(tk.END, "✅ 三个命令全部执行完毕！\n", "success")

    # 4) Check GitHub
    check_github_push(text_widget)

    text_widget.insert(tk.END, "\n" + "=" * 50 + "\n", "separator")
    text_widget.insert(tk.END, "🎉 博客更新流程全部完成！\n", "title")

    btn.config(state=tk.NORMAL, text="自动更新博客")


def start_update(btn, text_widget):
    """Start the update in a background thread."""
    t = threading.Thread(target=update_blog, args=(btn, text_widget), daemon=True)
    t.start()


def build_gui():
    root = tk.Tk()
    root.title("博客自动更新工具")
    root.geometry("860x620")
    root.resizable(True, True)

    try:
        root.iconbitmap(
            default=(
                os.path.join(os.path.dirname(__file__), "icon.ico")
                if hasattr(sys, "_MEIPASS")
                else ""
            )
        )
    except Exception:
        pass

    # Style
    root.configure(bg="#f0f2f5")

    # Title
    title_frame = tk.Frame(root, bg="#f0f2f5")
    title_frame.pack(pady=(16, 4))

    title_label = tk.Label(
        title_frame,
        text="博客自动更新工具",
        font=("Microsoft YaHei", 18, "bold"),
        bg="#f0f2f5",
        fg="#1a73e8",
    )
    title_label.pack()

    subtitle_label = tk.Label(
        title_frame,
        text="本地路径: " + GIT_DIR,
        font=("Microsoft YaHei", 9),
        bg="#f0f2f5",
        fg="#666",
    )
    subtitle_label.pack()

    # Button
    btn_frame = tk.Frame(root, bg="#f0f2f5")
    btn_frame.pack(pady=(10, 6))

    btn = tk.Button(
        btn_frame,
        text="自动更新博客",
        font=("Microsoft YaHei", 12, "bold"),
        bg="#1a73e8",
        fg="white",
        activebackground="#1557b0",
        activeforeground="white",
        padx=28,
        pady=8,
        cursor="hand2",
        relief=tk.FLAT,
        command=lambda: start_update(btn, output_text),
    )
    btn.pack()

    # Output area
    output_frame = tk.Frame(root, bg="#f0f2f5")
    output_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 16))

    output_text = scrolledtext.ScrolledText(
        output_frame,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#1e1e1e",
        fg="#d4d4d4",
        insertbackground="white",
        relief=tk.FLAT,
        borderwidth=6,
    )
    output_text.pack(fill=tk.BOTH, expand=True)

    # Text tags for colors
    output_text.tag_config("command", foreground="#569cd6")
    output_text.tag_config("output", foreground="#d4d4d4")
    output_text.tag_config("error", foreground="#f44747")
    output_text.tag_config("success", foreground="#4ec9b0")
    output_text.tag_config("warning", foreground="#ce9178")
    output_text.tag_config("info", foreground="#9cdcfe")
    output_text.tag_config("title", foreground="#c586c0", font=("Consolas", 11, "bold"))
    output_text.tag_config("separator", foreground="#6a9955")

    # Footer
    footer = tk.Label(
        root,
        text="提示: 首次使用时请确保已配置 Git 凭据，否则推送可能失败。",
        font=("Microsoft YaHei", 8),
        bg="#f0f2f5",
        fg="#999",
    )
    footer.pack(pady=(0, 8))

    root.mainloop()


if __name__ == "__main__":
    build_gui()
