# 参与贡献

本项目欢迎事实勘误、语言改进、无障碍建议、课堂反馈和构建修复。贡献不得包含儿童个人信息、账号凭据、未公开学校资料或无权使用的图片。

## 修改一章

1. 选择 `books/grade-3` 至 `books/grade-6` 中的目标分册。
2. 在该册 `chapters/` 编辑 Markdown，并遵守本册 `STYLE_GUIDE.md`。
3. 新术语首次出现时解释，图片提供有知识含义的中文替代文本。
4. 图内节点使用准确短中文，箭头尖端只接触模块边框。
5. 活动默认使用虚构数据，高风险动作必须有停止或人工确认。

## 增删和调整章节

阅读顺序由每册 `book-manifest.json` 的 `source_order` 管理。

- **新增**：创建章节文件，再添加唯一 `id`、章节号、单元、标题和相对路径。
- **删除**：移除清单条目，再删除不再使用的正文与资源。
- **调整**：移动清单条目并更新章节号、图号和交叉引用。
- **改标题**：优先保留稳定 `id`，避免 EPUB 锚点无故改变。

## 插图维护

四至六年级知识图的结构与中文节点在 `assets/illustrations/visuals.json`，顶部标题在 `labels.json`。先生成无标题底图，再从底图生成 EPUB JPEG 与本地印刷 PNG。

```bash
.venv/bin/python tools/generate_series_visuals.py --book-root books/grade-6
.venv/bin/python tools/annotate_illustrations.py --book-root books/grade-6
```

不要直接在成品图上反复叠字。逐张检查文字是否完整、连接线是否穿过节点、箭头是否进入文字框以及小尺寸阅读是否清楚。

## 本地检查

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_series.py
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

发布维护者还需执行：

```bash
.venv/bin/python tools/build_series.py --publish
.venv/bin/python tools/build_series.py --verify-dist
```

提交前检查暂存区没有 `.env`、令牌、密码、Cookie、会话、缓存、依赖目录、真实账号配置和儿童个人资料。

## 勘误格式

请提供提交号、年级、章节、原句、问题类型、可靠证据和建议改法。涉及安全问题时，不要在公开 Issue 中披露可被利用的细节。
