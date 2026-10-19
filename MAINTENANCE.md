# Profile 维护说明

## 页面结构

`README.md`：终端 Hero → 可折叠的 hardware/ 目录 → Embedded Systems → Contributions.exe → 个人兴趣。四个目录项仅保留项目名与技术关键词，职责和经历不在首页展开。

Hero 引用 `assets/terminal.svg`（940 × 316）和 `assets/terminal-narrow.svg`（400 × 350），以原生 `<picture>` 在 640px 及以下切换。两份 SVG 都是可直接编辑的文本与矢量图形，没有外部字体、脚本或图片依赖；使用系统等宽字体回退。只有末尾光标闪烁，不支持动画的查看器仍能显示全部内容。

`assets/folder.svg` 是 18 × 16 的原创像素文件夹，采用 2px 网格和透明底色，仅用于目录标题。目录使用 GitHub 原生 `<details open>` / `<summary>`，默认展开，可折叠；四个项目名不是链接，没有伪装成可打开的公开项目。目录下的分支字符和项目内容是正常 Markdown 文本，跟随 GitHub 主题，不增加第二个黑色终端窗口。

颜色延续深墨绿、奶油白、珊瑚红、灰绿与低饱和金色。终端输出需要同时维护宽屏和窄屏两个文件；不使用旧生成器重建它们。

项目关键词沿用已核实的项目资料，不把团队代码、设计指标或教学补全写成个人实测。当前未核实到四个项目各自的公开页面，所以不放项目链接。新增链接前确认目标无需登录可访问，且内容已获准公开。

## 保留资产

原有九份 SVG、`projects/`、`systems.md`、`tools/build_assets.py` 及字体文件原样保留。本轮首页不再引用海报、项目封面和 Save Point；确认原型后再决定是否清理。

`assets/fsbb.svg` 继续保存完整的通用 FSBB 拓扑示意：两个半桥中点由电感连接，各端口分别对公共回路接电容，正母线不直连；它不是实装图纸。本轮没有改画电路。

## 模板参考

终端窗口、提示符、输出层级与光标参考 [Typewriter Intro](https://github.com/beydemirfurkan/awesome-github-profile/tree/main/templates/02-animated/typewriter-intro)，原模板标注 CC0。采用独立布局和配色，不使用第三方打字服务。

[Pac-Man Graph](https://github.com/beydemirfurkan/awesome-github-profile/tree/main/templates/04-gamified/pacman-graph) 为确认后的首选；[Snake Eat Graph](https://github.com/beydemirfurkan/awesome-github-profile/tree/main/templates/04-gamified/snake-eat-graph) 仅作比较，默认不同时安装。

## Pac-Man 自动更新

README 在 Embedded Systems 下增加 `Contributions.exe`，用 `<picture>` 选择 output 分支的浅色／深色 SVG，不添加卡片背景。`查看原尺寸` 链接用于手机上查看全年宽图。Hero、hardware/ 目录、配色和兴趣区保持原样。

`.github/workflows/pacman.yml` 按每天 07:47 UTC（北京时间 15:47）更新，也支持手动触发及首次提交配置后的 main push。计划任务可能延迟。所有 Action 使用核验过的完整提交 SHA；生成器固定 v5.3.2，不使用模板中无效的 `theme` / `output` 输入。

生成作业只有 `contents: read`，上游通过 GITHUB_TOKEN 请求 `lls144` 的 GitHub GraphQL 贡献日历。发布作业单独拥有 `contents: write`；令牌权限不是单分支隔离，但发布命令只指向 output，且不使用 force push。只有生成及验证成功后才发布两个 SVG、`pacman-provenance.json` 和 `.pacman-managed` 管理标记。其他 output 文件保留，已有同名但未被本工作流管理的文件会导致发布中止。

`tools/pacman-network.cjs` 只通过该生成步骤的 NODE_OPTIONS 加载，允许 GitHub 贡献 API 请求，拒绝上游附带的作者站点统计与排行榜上报；没有修改上游生成器或配色。`tools/validate_pacman.py` 在上传和发布前检查两个 SVG 的格式、大小、动画及外部依赖。

### 数据与故障处理

生成器使用认证 GraphQL 贡献日历，不走无令牌的 REST 提交搜索回退。数据守卫验证每日数量与等级、完整日期数量、两种主题的日历一致性；HTTP 错误、GraphQL 错误、缺失数据或真实全零日历都会中止发布。全零不是请求失败，但无法产生真实吃点轨迹；需要检查账户 Private contributions 展示开关和提交统计资格，不填入模拟数据。

`pacman-provenance.json` 仅包含日期、匿名贡献数量／等级、数据 SHA-256、生成器版本、工作流提交及运行地址、两份 SVG 的 SHA-256，不包含仓库名称、提交内容、凭据或作者个人资料。验证器同时检查 Pac-Man 的移动轨迹与贡献格动画，防止只有张嘴的空图替换已发布动画。

账户展示私有贡献时，只公开匿名计数，不需要赋予工作流访问其他私有仓库的权限。主页仓库需要 Public 才能让匿名访客读取 README 与 output 资源；该设置与其他项目仓库的可见性无关。

### 运维

在 Actions 中手动运行 **Update Pac-Man contributions** 可刷新 output。先检查 generate 的日历摘要，再检查 publish 和 output 中的追溯文件；请求失败不会清空上一版图。每天 07:47 UTC 的计划只在默认分支工作流启用时生效，GitHub 可能延迟执行；公共仓库长期不活跃时 GitHub 也可能停用计划，届时需重新启用工作流。

与上游的差异仅在外围网络守卫、真实数据审计、SVG 验证及发布隔离；游戏逻辑、路径规划与浅深主题保持上游 v5.3.2 原版。没有把本地凭据交给第三方生成器。

## 预览与审阅资料

本地预览、模板源文件、诊断快照与公开前安全审查记录均在仓库外保存。页面截图只能验证布局；线上运行状态应以 Actions 结果、output 追溯文件和匿名 HTTP 访问为准。
