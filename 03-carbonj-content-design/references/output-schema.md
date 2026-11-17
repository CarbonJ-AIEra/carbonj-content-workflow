# 内部校验结构与最终预览

以下 JSON 使用 `schemaVersion: 1`，只作为生成过程中的临时结构，用于事实边界校验和渲染最终 Markdown。默认不得把它作为交付物保留在输入目录中。

```json
{
  "schemaVersion": 1,
  "source": {"inputType": "video+subtitle", "videoPath": "/absolute/video.mp4", "transcriptPath": "/absolute/video.srt", "language": "zh-CN"},
  "contentBrief": {
    "subject": "视频主题",
    "audience": "目标受众",
    "painPoint": "具体问题",
    "outcome": "视频展示的结果",
    "evidence": [{"claim": "陈述", "status": "verified", "source": "字幕或口播稿依据"}],
    "prohibitedClaims": ["不能写入成品的夸张或未确认说法"]
  },
  "platforms": {
    "xiaohongshu": {"title": "", "body": "", "searchKeywords": [], "topics": []},
    "douyin": {"title": "", "topics": []},
    "bilibili": {"title": "", "description": "", "tags": []},
    "wechat_channels": {"shortTitle": "", "coreTheory": "", "description": "", "hashtags": []},
    "x": {"post": "", "hashtags": []},
    "youtube": {"title": "", "description": "", "chapters": [], "keywords": [], "hashtags": []},
    "wechat_official": {"title": "", "digest": "", "body": "", "keywords": []}
  },
  "review": {"needsUserConfirmation": [], "notes": []}
}
```

`evidence.status` 只能是 `verified`、`attributed` 或 `uncertain`。涉及收入、销量、排名、百分比、用户规模或比较性结论时必须进入 `evidence`。

`source` 至少包含 `videoPath` 或 `transcriptPath` 之一。SRT 入口找到同名视频后使用 `inputType: video+subtitle`；只有字幕时使用 `inputType: subtitle-only`，可以生成七平台内容，但不能导出可发布视频包。

小红书 `title` 是发布搜索标题，不是封面标题；`searchKeywords` 是需要自然出现在标题或正文里的检索词。小红书正文以约 200 字为目标。抖音没有 `body`。视频号必须同时提供短标题、核心理论和结构化简介。

所有话题数组的元素都包含前导 `#`，例如 `["#AI工具", "#AISkill"]`。Markdown 预览将它们用空格连接，不能使用顿号。YouTube 和公众号的 `keywords` 除外，它们不是显示话题。

## 默认交付物

默认只生成一个文件，并直接放在输入视频或字幕旁边：

```text
<输入stem>_七平台内容预览.md
```

不得默认创建 `.content-design` 目录，也不得留下 `content-package.json`、`source-analysis.json`、`video-publisher-package.json` 或其他中间文件。临时 JSON 校验通过并渲染 Markdown 后应留在临时目录或清除。

最终 Markdown 使用下面的结构：

```markdown
# 七平台内容预览

## 1. 小红书
### 搜索标题
### 正文
### 话题

## 2. 抖音
### 标题
### 话题

## 3. B站
### 标题
### 简介
### 标签

## 4. 视频号
### 短标题
### 核心理论
### 结构化简介
### 话题

## 5. X
### 正文
### Hashtags

## 6. YouTube
### 标题
### 简介
### 章节
### 关键词
### Hashtags

## 7. 公众号
### 标题
### 摘要
### 正文
### 关键词
```

预览必须包含每个平台可直接使用的完整成品：完整标题、完整正文或简介、全部话题标签、YouTube 章节与关键词，以及完整公众号文章。不能只写摘要、生成说明或“视频从某个问题展开”一类占位概述。抖音是唯一不展示正文的默认平台，只保留标题和话题。

## 可选发布包兼容

只有用户明确要求发布兼容包时，才使用 `validate_package.py --publisher-output` 生成当前 `video-publisher` 可读取的四平台字段：`xhsTitle`、`xhsTopics`、`douyinTitle`、`douyinDescription`、`douyinTopics`、`bilibiliTitle`、`bilibiliDescription`、`bilibiliTags`、`wechatTitle`、`wechatShortTitle`、`wechatDescription` 和 `wechatTags`。发布包会自动去掉标签开头的 `#`。抖音 `douyinDescription` 保持空字符串。

本 Skill 不负责封面，因此兼容发布包显式写入 `cover.uploadCustomCover: false`，避免 `video-publisher` 自动发现同目录但比例不合格或未经确认的封面。用户另行确认封面后，再由封面或发布流程显式覆盖该字段。

小红书正文会额外保存在 `xiaohongshuBody` 中，避免内容丢失；当前发布器是否写入该字段需要在实际草稿流程中另行验证。
