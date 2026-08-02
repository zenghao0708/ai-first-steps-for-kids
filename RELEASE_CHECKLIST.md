# 发版前检查清单

## 四册内容范围

- [x] 三至六年级各有独立 manifest、12 章正文和完整前后置内容。
- [x] 每册包含 40 个术语、12 张任务卡、成人指南和直接参考链接。
- [x] 四至六年级每章包含两张 2000×1500 中文高清插图。
- [x] 图片替代文本、中文标注清单、源文件和 EPUB 引用保持一致。
- [x] 六年级覆盖工具调用、智能体、端侧 AI、RAG、安全、监督和社会责任。

## CI 等价命令

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_series.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/build_series.py --verify-dist
git diff --check
```

## 2026-08-02 实测结果

- [x] 四册 Markdown 与 EPUB 均可从各自 manifest 独立构建。
- [x] 四册 EPUB 的 mimetype、container、OPF、spine、nav、NCX、资源引用和 XML 可解析。
- [x] 自动测试 11 项通过，覆盖章节结构、术语、任务卡、图片尺寸、替代文本和中文标注。
- [x] 四至六年级知识图视觉抽检通过，箭头不进入节点，文字无明显溢出或遮挡。
- [x] `dist/grade-3` 至 `dist/grade-6` 与当前源码构建结果逐字节一致。
- [x] `dist/SHA256SUMS` 覆盖四册发布文件和三年级兼容下载别名。
- [x] 暂存前执行敏感文件、缓存、依赖和凭据检查。

## 发布人工门槛

- [ ] 每个年级至少 3 名目标年龄读者在监护人同意下完成试读。
- [ ] 至少 1 名小学教师或少儿编辑检查阅读难度和活动安全。
- [ ] 至少 1 名 AI 工程师复核技术边界、示例和参考资料。
- [ ] 根据试读证据修订，并记录版本、日期和影响分册。

自动检查不能替代真实读者测试。人工门槛完成后，再统一创建 GitHub Release。
