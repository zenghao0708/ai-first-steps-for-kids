# AI 小侦探开源课程系列

面向小学三至六年级的人工智能启蒙与进阶课程。四册沿同一组校园角色螺旋上升：从观察 AI 现象与安全习惯，逐步进入数据、模型、RAG、智能体、端侧 AI、系统评测和责任设计。

## 下载电子书

| 年级 | 书名 | 学习主线 | EPUB |
| --- | --- | --- | --- |
| 三年级 | 《AI 小侦探》 | 感知 AI、机器学习、生成式 AI、核验与安全 | [下载](https://github.com/zenghao0708/ai-first-steps-for-kids/raw/main/dist/grade-3/ai-detective-grade-3.epub) |
| 四年级 | 《AI 小工程师》 | 数据清理、特征、规则、决策树、测试与公平 | [下载](https://github.com/zenghao0708/ai-first-steps-for-kids/raw/main/dist/grade-4/ai-engineer-grade-4.epub) |
| 五年级 | 《AI 模型训练营》 | 向量、神经网络、注意力、RAG、多模态与评测 | [下载](https://github.com/zenghao0708/ai-first-steps-for-kids/raw/main/dist/grade-5/ai-model-lab-grade-5.epub) |
| 六年级 | 《AI 系统设计师》 | 工具调用、智能体、端侧 AI、红队与责任治理 | [下载](https://github.com/zenghao0708/ai-first-steps-for-kids/raw/main/dist/grade-6/ai-system-designer-grade-6.epub) |

文件校验值见 [dist/SHA256SUMS](dist/SHA256SUMS)。EPUB 3 阅读版包含分章目录、稳定锚点、封面和内嵌高清中文插图，支持阅读器中的目录、书签和笔记功能。

旧的三年级下载地址 `dist/ai-detective.epub` 作为兼容别名继续保留，内容与三年级目录中的文件完全一致。

## 课程阶梯

- 三年级：观察现象，用自己的话解释输入、处理和输出，养成核验与求助习惯。
- 四年级：整理数据、比较规则与学习方法，用测试证据改进分类系统。
- 五年级：理解模型表示与应用链路，完成带检索、引用和分层评测的知识助手。
- 六年级：把模型、数据、工具、权限、日志和人组成系统，用失败证据参加责任答辩。

完整设计依据和逐册大纲见 [series/CURRICULUM.md](series/CURRICULUM.md)，统一角色与插图规范见 [series/VISUAL_GUIDE.md](series/VISUAL_GUIDE.md)。

## 仓库结构

```text
books/
  grade-3/                 《AI 小侦探》
  grade-4/                 《AI 小工程师》
  grade-5/                 《AI 模型训练营》
  grade-6/                 《AI 系统设计师》
    book-manifest.json     本册元信息、章节顺序和质量要求
    front-matter/          书名页与导读
    chapters/              12 章正文
    back-matter/           40 词术语表、任务卡、成人指南、参考资料
    assets/                封面和中文高清插图
series/                    全系列课程与视觉规范
tools/                     构建、插图标注和发布工具
tests/                     四册共用质量检查
dist/grade-*/              可直接下载的 EPUB
```

每册的阅读顺序只由该册 `book-manifest.json` 管理。新增、删除、重排或改名章节时，编辑对应清单，不需要修改 EPUB 构建器。

## 本地构建

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_series.py
.venv/bin/python -m unittest discover -s tests -v
```

构建结果位于 `build/*.md` 和 `build/*.epub`。发布维护者使用下面的命令一次更新四册下载文件与 SHA-256：

```bash
.venv/bin/python tools/build_series.py --publish
.venv/bin/python tools/build_series.py --verify-dist
```

修改四至六年级知识图配置后，使用对应分册路径重新生成；三年级历史插图继续由中文标注脚本维护。

```bash
.venv/bin/python tools/generate_series_visuals.py --book-root books/grade-6
.venv/bin/python tools/annotate_illustrations.py --book-root books/grade-6
```

## 内容与安全原则

- 先讲生活问题，再解释技术名称；不把 AI 拟人化或描述成永远正确。
- 代码、实验和任务必须可复现；在线能力只作为成人控制下的扩展。
- 插图承担解释任务，关键节点使用准确中文，连线接触边框但不穿过节点或文字。
- 儿童活动默认使用虚构数据，不提交真实姓名、照片、声音、位置、账号或校内资料。
- 高年级项目必须有边界、失败案例、停止条件、替代流程和人工责任人。

参与方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，发版门槛见 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)。

## 授权

- 书稿、任务卡、插画和 EPUB：[CC BY-NC-SA 4.0](LICENSE-CONTENT.md)
- 构建工具与测试代码：[MIT License](LICENSE-CODE)

详细边界见 [LICENSE.md](LICENSE.md)。商业出版或付费课程需另行取得授权。
