# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run GUI app**: `python blog_updater.py`
- **Run MCP server**: `python mcp_blog_updater.py`
- **Build EXE**: `python build_exe.py` (outputs to `dist/博客自动更新工具.exe`)
- **Test MCP sync function directly**: `python -c "from mcp_blog_updater import update_blog_sync; print(update_blog_sync())"`

## Architecture

This is a Windows desktop tool that automates updating a GitHub Pages blog. The core pipeline is:

1. **Copy images** from `_posts/images` to `images` in the blog repo
2. **Git commit & push** the blog repo with message "update blog"
3. **Verify** via GitHub API that the push succeeded

Three entry points, all sharing the same sync logic (`update_blog_sync` in `mcp_blog_updater.py`):
- **`blog_updater.py`** — tkinter GUI with a single button, real-time command output in a scrollable text widget
- **`mcp_blog_updater.py`** — MCP (Model Context Protocol) server exposing `update_blog` tool via stdio transport
- **`博客自动更新工具.exe`** — PyInstaller `--onefile --windowed` build of `blog_updater.py`

### Key hardcoded paths (specific to dev machine)
- Blog repo: `D:\github_page\wuyinshuang.github.io`
- Python 3.14 path in `run_mcp_blog_updater.bat`: `C:\Users\wys19\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Git remote: `https://github.com/wuyinshuang/blog-update-auto.git` (this project)
- Blog site remote: `https://github.com/wuyinshuang/wuyinshuang.github.io` (verified after push)

### Dependencies
- No `requirements.txt` — `mcp` package is installed on demand (`pip install mcp`) inside the script
- PyInstaller is installed on demand by `build_exe.py`
- Standard library only for the GUI version: tkinter, subprocess, shutil, threading, etc.

## Additional instructions
