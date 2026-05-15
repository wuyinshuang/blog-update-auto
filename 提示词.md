# 博客自动发布桌面应用

## 概述
开发一个 Windows 桌面应用程序（生成 exe），双击运行即可打开 GUI 界面，界面中包含「自动更新博客」按钮，一键完成博客资源同步、Git 提交推送、推送结果验证。

## 功能需求

### 1. 图片同步
- 将 `D:\github_page\wuyinshuang.github.io\_posts\images` 目录下的**所有文件**复制到 `D:\github_page\wuyinshuang.github.io\images`
- 同名文件**跳过**（不覆盖），只复制不存在的文件

### 2. Git 自动提交与推送
进入 `D:\github_page\wuyinshuang.github.io` 目录，依次执行以下命令：
```bash
git add .
git commit -m "update blog"
git push
```

### 3. 日志展示
- 在界面上**实时展示**上述三条命令的执行过程及输出结果

### 4. 完成通知
- 三条命令全部执行完毕后，在界面上提示用户「执行完毕」

### 5. 推送验证
- 访问 `https://github.com/wuyinshuang/wuyinshuang.github.io`，检查最新推送是否成功
- 将验证结果展示在界面上

## 技术要求
- 使用 Python + tkinter / PyQt 等框架开发
- 打包为独立的 `.exe` 文件（可使用 PyInstaller）
- 支持 Windows 环境运行
