# AI 小侦探

给三年级孩子的人工智能第一课。

这是一本正在创作中的少儿 AI 科普书。它用校园、家庭和游戏中的故事，解释人工智能、机器学习、数据、图像识别、语音识别、生成式 AI、大语言模型、机器人以及 AI 安全等基础概念。

**电子书**：[下载 EPUB 阅读版](https://github.com/zenghao0708/ai-first-steps-for-kids/raw/main/dist/ai-detective.epub) · [SHA-256 校验值](dist/SHA256SUMS)

## 读者

- 主要读者：小学三年级学生（约 8—10 岁）
- 共读者：家长、信息科技教师和科学教师
- 阅读前提：能独立阅读常见汉字，不要求数学或编程基础

## 内容原则

- 先讲生活问题，再讲技术名字。
- 一次只解释一个关键概念。
- 用故事、比喻和动手实验帮助理解，但明确说明比喻的边界。
- 不把 AI 写成“会思考的人”，也不暗示它永远正确。
- 每章至少配一幅承担解释任务的原创插画。
- 涉及拍照、录音和上网时，明确提醒孩子先征得家长或老师同意。

## 目录结构

```text
book/
  book-manifest.json       书稿顺序与元信息
  OUTLINE.md               全书大纲
  STYLE_GUIDE.md           写作和术语规范
  front-matter/            书名页、导读
  chapters/                各章正文
  back-matter/             术语表、活动材料
  assets/
    storyboards/           漫画分镜
    prompts/               插画生成提示词
    illustrations/
      source/              可编辑高清源文件（默认不提交大型工程文件）
      print/               印刷用图片
      epub/                电子书优化图片
tools/                     构建与检查工具
tests/                     自动化测试
comic/                     漫画分析、角色表、分镜和生成提示词
dist/                      已校验的 EPUB 阅读版与校验值
```

## 构建与检查

```bash
python3 -m pip install -r requirements.txt
python3 tools/build_book.py
python3 tools/build_epub.py
python3 -m unittest discover -s tests
```

构建结果输出到 `build/book.md` 和 `build/ai-detective.epub`。EPUB 包含分章目录、稳定锚点、封面和内嵌高清插图，可在支持 EPUB 3 的阅读器中使用目录、书签和笔记功能。章节增删和重排只需要修改 `book/book-manifest.json`。

发布前将校验通过的文件复制到 `dist/`，并用下面的命令核对下载文件：

```bash
shasum -a 256 -c dist/SHA256SUMS
```

## 当前进度

- 已完成读者定位、写作规范和 12 章大纲。
- 已完成全部 12 章正文，覆盖 AI、机器学习、测试、感知、生成式 AI、大语言模型、提示设计、幻觉核验、机器人、安全与综合设计。
- 已建立统一角色参考表，完成 27 幅正式插画及对应分镜、提示词；知识图均配有中文说明或正文图注。
- EPUB/GitHub 阅读版插画统一为 2000×1500 高质量 JPEG；印刷 PNG 在本地生成目录维护。

在线仓库：<https://github.com/zenghao0708/ai-first-steps-for-kids>

## 授权说明

- 书稿、任务卡、插画和 EPUB： [CC BY-NC-SA 4.0](LICENSE-CONTENT.md)
- 构建工具与测试代码：[MIT License](LICENSE-CODE)

详细边界见 [LICENSE.md](LICENSE.md)。商业出版或付费课程需另行取得授权。
