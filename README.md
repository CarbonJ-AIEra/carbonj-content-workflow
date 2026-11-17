# CarbonJ Content Workflow

一组面向视频内容创作的 CarbonJ Skills：从视频主题讲解、平台文案，到多尺寸封面，覆盖内容生产的主要环节。每个 Skill 可以单独使用，也可以按下方工作流组合使用。

## 包含的 Skills

### 01 · CarbonJ SVG HTML

路径：[`01-carbonj-svg-html/`](01-carbonj-svg-html/)

把主题、稿件或资料制作成可编辑的 SVG HTML。支持纵向滚动的长文页面和 PPT 式逐页演示，并提供多种视觉风格；生成后可以在页面原位编辑文字和图形，再导出 HTML 或 SVG。适合先把视频主题整理成一份可阅读、可讲解或可分享的内容成品。

### 02 · CarbonJ Cover

路径：[`02-carbonj-cover/`](02-carbonj-cover/)

根据标题与视频内容分析画面、选择合适的视觉素材，并生成适配不同平台的封面图。默认覆盖小红书 3:4、B 站 4:3 和 16:9 画幅；Skill 也包含封面规则、素材和生成脚本。可使用 Agent 自主流程，或使用脚本流程。

### 03 · CarbonJ Content Design

路径：[`03-carbonj-content-design/`](03-carbonj-content-design/)

从视频、字幕或口播稿提取事实与主题，再按各平台的内容习惯生成搜索标题、正文和标签。默认生成小红书、抖音、B 站、视频号、X、YouTube 与公众号七个平台的内容，并保留平台间的表达差异。

## 建议工作流

```text
视频 + 字幕 / 口播稿
        │
        ├── 01 CarbonJ SVG HTML：整理成可编辑长页面或 PPT 式讲解材料
        ├── 02 CarbonJ Cover：结合标题与视频画面生成平台尺寸封面
        └── 03 Content Design：按平台生成搜索标题、正文和标签
```

1. 准备视频以及同名字幕，或准备完整口播稿。字幕和口播稿帮助确认事实，视频提供画面证据。
2. 使用 **Content Design** 生成各平台的标题、正文和标签，并检查事实、关键词和平台格式。
3. 使用 **CarbonJ Cover**，提供确认后的标题和视频，生成对应平台尺寸的封面。
4. 如需解释视频主题、制作教程或演示材料，把整理好的主题与资料交给 **SVG HTML**，选择长页面或 PPT 式演示及视觉风格，完成后可继续编辑。
5. 将封面、平台文案与讲解材料分别用于对应的发布或分享场景。各 Skill 默认只生成本地内容，不会自动发布。

三个 Skill 可以独立运行；不需要讲解材料时可跳过 SVG HTML，需要先制作讲解内容时也可以先从 SVG HTML 开始。

## 安装

将需要的子目录复制到对应 Agent 的 Skills 目录即可。以 Codex 为例：

```bash
mkdir -p ~/.codex/skills
cp -R 01-carbonj-svg-html ~/.codex/skills/carbonj-svg-html
cp -R 02-carbonj-cover ~/.codex/skills/carbonj-cover
cp -R 03-carbonj-content-design ~/.codex/skills/carbonj-content-design
```

安装后刷新 Skills 列表或重启客户端。每项 Skill 的详细依赖、输入方式和参数见其子目录 `SKILL.md` 及 README。

## 许可证与第三方资产

本组合仓库及原创内容采用 [MIT License](LICENSE) © 2026 Carbon-J。各子 Skill 随附的 `LICENSE`、`NOTICE` 和资产说明也一并保留；字体、商标及其他第三方素材按各自来源的许可和归属说明使用。
