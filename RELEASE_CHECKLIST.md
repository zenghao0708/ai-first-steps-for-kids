# 发版前检查清单

## 内容范围

- [x] 12 章正文全部进入 manifest。
- [x] 40 个术语进入电子书附录。
- [x] 12 张任务卡与章节一一对应。
- [x] 家长教师指南与事实核验参考资料已加入。
- [x] 27 幅章节插图和 1 幅封面进入 EPUB。
- [x] 图内关键知识配中文标签，正文图片有替代文本和图注。

## 等价命令

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/annotate_illustrations.py
.venv/bin/python tools/build_book.py
.venv/bin/python tools/build_epub.py
.venv/bin/python tools/build_epub.py --validate build/ai-detective.epub
.venv/bin/python -m unittest discover -s tests -v
git diff --check
shasum -a 256 -c dist/SHA256SUMS
```

## 2026-08-02 实测结果

- [x] Markdown 构建：18 个源文件，约 4.6 万字符。
- [x] EPUB 构建：18 个源文件、28 幅图片、53 个包内文件。
- [x] EPUB 结构：mimetype、container、OPF、spine、nav、NCX、资源引用和 XML 解析通过。
- [x] 自动测试：11 项通过，包含 27 幅章节插图与中文标注清单的一致性检查。
- [x] 可复现性：连续两次构建的 EPUB 二进制一致。
- [x] 插图视觉检查：27 幅正文插图逐张检查，标题、图内补充标签和原有中文均可读且未溢出。
- [x] EPUB 图片检查：包内 27 幅正文插图和 1 幅封面均与构建源文件逐字节一致，中文标注正常嵌入。
- [x] 敏感文件检查：暂存区不包含 `.env`、凭据、会话、缓存和依赖目录。

## 发布人工门槛

- [ ] 至少 3 名 8—10 岁读者在监护人同意下完成试读。
- [ ] 至少 1 名小学教师或少儿编辑检查阅读难度和任务安全。
- [ ] 至少 1 名 AI 工程师复核技术边界与术语。
- [ ] 将试读发现按证据修订，并记录版本与日期。

自动检查不能替代真实读者测试。完成上述人工门槛后，再创建首个 GitHub Release。
