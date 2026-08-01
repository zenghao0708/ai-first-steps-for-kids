# 参与贡献

本项目欢迎事实勘误、语言改进、无障碍建议、任务卡反馈和构建修复。贡献内容不得包含儿童个人信息、账号凭据、未公开学校资料或无权使用的图片。

## 修改一章

1. 在 `book/chapters/` 中编辑对应 Markdown。
2. 保留漫画开场、AI 侦探任务、动手试一试、侦探笔记和给大人的话。
3. 新术语第一次出现时解释含义，避免把 AI 拟人化。
4. 图片使用 2000×1500 阅读版 JPEG，提供说明知识的替代文本。
5. 图内关键流程配准确短中文，箭头尖端只接触模块边框。

## 新增、删除或调整章节

所有阅读顺序由 `book/book-manifest.json` 管理。

- **新增**：创建章节文件，再向 `source_order` 添加唯一 `id`、章节号、单元、标题和路径。
- **删除**：从 `source_order` 移除条目，再删除不再使用的正文与资源。
- **调整**：移动条目并更新章节号、图号和正文交叉引用。
- **改标题**：优先保留稳定 `id`，这样 EPUB 文件名和外部链接不会无故改变。

## 本地检查

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_book.py
.venv/bin/python tools/build_epub.py
.venv/bin/python tools/build_epub.py --validate build/ai-detective.epub
.venv/bin/python -m unittest discover -s tests -v
```

提交前运行 `git diff --check`，并检查暂存区中没有 `.env`、令牌、密码、Cookie、会话文件、缓存、依赖目录和儿童个人资料。

## 勘误格式

请提供版本或提交号、章节、原句、问题类型、可靠证据和建议改法。涉及安全问题时，不要在公开 Issue 中披露可被利用的细节。
