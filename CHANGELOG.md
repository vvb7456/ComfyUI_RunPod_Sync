# Changelog

本文件记录各正式版本的变更。Release 发布时由 release.yml 自动提取对应 tag 的段落作为 Release 说明。

## v0.7.1 — 2026-09-06

### 新增

- 模型类别 badge 单一事实源：`normalizeModelCategory` / `modelCategoryColor` / `modelCategoryLabel` 统一本地索引、Civitai、HF 白名单、下载任务四条数据管线的 type 归一与文案，迁移 5 个组件移除各自映射表，修复部分类别 badge 无色全灰
- 下载量紧凑格式化 `fmtCompact`（56.8k / 1.2M），Civitai 卡片 meta 行启用
- 页面工具栏吸顶：新增 PageTopStack 组件，Models / ComfyUI 页各 tab 的 SectionToolbar（含未保存提示条）通过 Teleport 挂到顶部栈随页面吸顶

### 重构

- 全局产物 / 素材卡统一 3:4 竖版比例（Dashboard 画廊、历史面板、批量预览、LoRA 卡、模型选择器、模型卡），网格列宽收窄保证一屏至少两行，Civitai 缩略图升级 width=550 适配竖版高度
- 字体栈规范化：移除 Google Fonts 外链依赖，全局 font-family 改为西文优先 + 系统原生无衬线回退；新增 `--font-tabular` 变量修复等宽混排时汉字错误回退为宋体衬线
- 简化诊断 / 历史入口标题文案

### 修复

- 页面切换 transform 入场动画引发的吸顶首帧渲染丢失与文档级假滚动条（page-fade 改 opacity-only；DropdownMenu 弃用 `:global()` 规避 compiler-sfc 丢弃后续选择器）
- Release 说明改用 CHANGELOG.md 自动提取（v0.7.0 起），缺失对应段落则发布失败

## v0.7.0 — 2026-08-30

### 新增

- 侧边栏按功能分组导航（工作区 / 服务 / 连接 / 系统），下拉菜单重构为悬浮级联子菜单，支持键盘导航与移动端视图切换
- 移动端双层布局：汉堡菜单内嵌标题栏，TabSwitcher 双行吸顶，未保存提示条吸附位置随双行高度校准
- 队列 / 历史抽屉支持 `?panel=` 深链直开
- 服务跳转地址离线检测与端口兜底（`/api/overview` 与 `/api/comfyui/status` 返回实际端口）
- Release 分发机制：tag push 自动构建并发布完整部署包 `comfycarry-dist.tar.gz`，bootstrap 与面板内置更新统一以 latest Release 为更新源

### 重构

- 移除全局固定顶栏，标题与操作下放至各页面首行并吸顶；桌面 / 移动端布局统一
- Dashboard 拆分为 Hero / Tasks / Services / Gallery / Diagnostics 五个子组件，画廊接入生成队列 store，消除私有请求
- 控件高度基准统一（34px / 28px），SegmentedControl 接入滑动指示器，全局 200ms 过渡动效
- 主题规范化：硬编码颜色改为设计变量与 color-mix，登录页浅色主题 Modern Neutral 化
- UsageBar 统一品牌主色，移除孤儿组件 ProgressBar
- 热更新改为逐项 staged 交换（备份 - 落位 - 回滚），更新中断不再留下半新半旧状态

### 修复

- 提示词设置在组件重建后误报未保存（dirty 快照移至模块级）
- 移动端未保存提示条吸顶时与标签行重叠
- Dashboard 画廊在新增产物时整行卡片重建、服务总数异常时回退为固定值、服务运行时长时钟偏差时显示负数、离开页面后延迟任务仍触发请求
- 下拉菜单鼠标与键盘混合操作时，刚展开的子菜单被悬挂的关闭倒计时误关
- 热更新下载失败残留临时文件；bootstrap 版本记录的 commit 写入分支名而非真实 SHA
- 更新检查改为语义化版本比对，与 tag 发布机制对齐

### 变更

- 图像任务默认架构由 SDXL 切换为 SD 1.5
- main 分支 push 不再触发任何发布，commit 与 Release 完全解耦
