---
name: carbonj-svg-html
license: MIT
description: Create editable SVG HTML in two formats, a vertically scrolling long webpage or a PPT-style slide deck. Use for Chinese HTML presentations, long-form explainers, style showcases and vector content that users can edit directly in a browser. Every invocation starts by asking the user to choose long HTML or PPT-style slides, followed by visual style selection. Show actual compositions for Green grid, refined Hermès-orange, multicolor macaron, high-end consulting and Anthropic-inspired. Default to Source Han Sans / Noto Sans SC with weights adjusted to hierarchy.
---

# CarbonJ SVG HTML

Build editable Chinese content as a long webpage or a PPT-style deck. Preserve text and vector graphics as individual elements. Provide direct on-canvas text editing, shape fill controls and HTML / SVG exports.

## Start every content task

1. Ask which format the user wants for this invocation. Offer **长 HTML，纵向滚动阅读** and **PPT 式，逐页翻页演示**. If the user has already chosen a format in this invocation, use that choice.
2. Show actual compositions for all five visual systems using the same topic. Make the style names prominent and the layout differences immediately visible. Use a simultaneous grid with several substantial examples visible together. Use enough space to show typography, layout and graphics clearly.
3. Ask which visual style to use. Allow a combination or a new direction. Wait for the selection before producing the full content. A style named by the user in this invocation counts as their selection.
4. Include a font specimen when presenting design choices. Show the same Chinese headline and body copy in the default Source Han Sans / Noto Sans SC and optional font treatments. Keep Source Han Sans as the default unless the user chooses another font.
5. Use the topic, audience, source materials and size already provided. Ask for missing information only when it materially changes the result.

## Long HTML

- Build a responsive page with continuous vertical scrolling, a real document flow and comfortable reading widths. Sections may have different heights according to their content.
- Let the first screen communicate the topic immediately. For a Skill introduction or a style showcase, lead with several clearly named, substantial style examples visible together. Arrange all five examples in a dense but readable grid so the range looks broad at first glance.
- Make the five styles differ in composition, typography hierarchy, palette and graphics. Use the reference systems in `references/style-systems.md`.
- Use editable HTML text for flowing prose and inline SVG for illustrations, comparisons, charts and diagrams. Native HTML text uses `data-editable-html` and becomes directly contenteditable in edit mode.
- Keep SVG text as native `<text>/<tspan>` and mark it with `data-editable-text`. Export individual SVG figures from the page.
- Keep document scrolling available while editing. Use a compact persistent editing toolbar with HTML export and selected-figure SVG export.
- Use the long-page example `assets/long-page-example.html` as a reference for structure and interaction.
- When introducing the two output formats, embed working long-page and PPT-style previews in the same page. Provide in-place switching, expansion and fullscreen controls. Use self-contained srcdoc snapshots, and remove the showcase from its own long-page snapshot to prevent recursive embedding.

## PPT-style HTML

- Build a navigable deck with one separate inline SVG canvas per slide.
- Default to 16:9 with `viewBox="0 0 1600 900"`. Follow a user-requested ratio.
- Compose each slide around one main message. Include previous / next, left / right arrow, PageUp / PageDown and Home / End navigation.
- Use `assets/starter.html` as the structural starting point.

## Typography and style

- Read `references/style-systems.md` for the five palettes and layout directions.
- Build visually varied compositions using relevant charts, metric cards, tables, timelines, process diagrams and illustrations. Style-showcase examples should demonstrate this variety in every visual system. Label invented sample values as demonstration data and keep totals and percentages consistent.
- Default to Source Han Sans / Noto Sans SC in every style. Use 800–900 for cover headlines, 700–800 for section headings, 400–500 for body text and 500–600 for labels. Adapt size to the actual viewport and chosen format.
- Offer Noto Serif SC for optional editorial headlines, LXGW WenKai for short warm emphasis and Ma Shan Zheng for a few expressive display characters. Apply these only when selected.
- Load web fonts from a reliable source with a system fallback. State when exact font rendering needs an internet connection.
- Organize content around a clear question or conclusion, concrete explanation or examples, and a useful next action. Use the user's supplied evidence for factual claims.

## Editing and export

- Reuse `assets/editor-runtime.js` and inline it into the final HTML. The runtime supports `body data-layout="long"` and slide-deck mode.
- Let users click HTML text and type in the element directly. For native SVG text, place a matching inline editor over the original text and write changes into `<text>/<tspan>` immediately.
- Keep editing on the canvas. Use the persistent toolbar for object fill color, SVG export and HTML export. Remove temporary editing overlays before exporting.
- Mark editable shapes with `data-editable-shape`. Keep each meaningful vector element separately editable. Use native SVG geometry for diagrams and charts.
- Export HTML with edited content and inline interaction code retained. For SVG export, preserve text and shapes and resolve CSS typography and colors into the SVG.
- Keep screenshots and photos as separate image layers when the user supplies or requests them.

## Delivery

Save the finished HTML in the requested location, or a dated topic folder in the current workspace. Check content, rendering and editing through the normal entry points. Report what was actually checked and any remaining verification limits. Give the absolute path and identify whether the result is long HTML or PPT-style HTML. Publish or upload only when the user asks.
