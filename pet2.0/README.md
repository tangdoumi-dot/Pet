# pet2.0：修复宠物点击穿透、无法拖动的 bug

本目录保存已在本机验证有效的 Windows 宠物窗口修复工具，不覆盖仓库中 pet 1.0 的文件。这里的 2.0 是工具包版本，不表示精灵图已升级为 v2 格式。

## 修复内容

修复了 Codex 宠物点击落到桌面、无法拖动的问题：定位当前唯一可见的 Codex 宠物工具窗口，清除 `WS_EX_LAYERED` 标志并刷新窗口。用户已确认手动修复后可以点击和拖动。

这是对 Codex 桌面端问题的临时兼容修复，不修改 Codex 安装文件、宠物图像或原有配置。对应故障报告：https://github.com/openai/codex/issues/43200 。本机验证版本为 `26.901.6511.0`，其他版本未保证兼容。

## 使用方法

- 手动修复：保持 Codex 和宠物窗口打开，双击 `fix-pet-click-through.cmd`，立即修复一次。
- 启动时修复：双击 `launch-codex-pet-fix.cmd` 打开 Codex，等待 8 秒后检查并修复一次，随后进程退出。
- 取消等待中的启动修复：运行 `disable-pet-auto-fix.cmd`。
- 撤销图层调整：运行 `restore-pet-window-style.cmd`。
- 只读检查：通过 Python 运行 `fix-pet-click-through.py --check`。

没有 Windows 登录自启动、三秒轮询或常驻后台进程。直接使用原有商店入口打开 Codex，不会触发启动修复。启动较慢、8 秒后仍无唯一宠物窗口时，本次检查会跳过；同一次运行中窗口重建后若复发，可再次手动修复。

## 运行要求与限制

需要 Windows 和 Python 3。CMD 启动器默认使用 `%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python` 下的 `python.exe` / `pythonw.exe`；其他电脑若没有该运行时，需要修改路径，或使用自己的 Python 3 运行脚本。脚本只使用标准库。

修复可能让宠物周围的透明区域也接收点击；遇到影响时可使用撤销工具恢复。未找到唯一窗口时不执行修改。

`watch-pet-window.py` 保留历史文件名，但当前实现只执行一次，不循环检查。诊断结果写入本目录的 `pet-window-backups/watcher-status.json`，已通过本目录 `.gitignore` 排除，不上传个人运行信息。
