const zh = {
  // Header
  "app.title": "出行决策 Agent",
  "app.subtitle": "运行在 EdgeOne Makers 上，接入高德地图实时数据",

  // Empty state
  "empty.title": "出行决策 Agent",
  "empty.hint": "我是出行决策 Agent：告诉我你在哪儿、想逛哪些品牌，我会检索附近的商场、核对门店、比较距离，再给你推荐。",
  "empty.features": "高德地图 · 门店核对 · 距离比较 · Session Memory",

  // Chat input
  "chat.placeholder": "发消息…  ⏎ 发送 · Shift+⏎ 换行",
  "chat.hint": "由 OpenAI Agents SDK + EdgeOne Makers + 高德地图驱动",

  // Preset questions
  "preset.1": "我在红莲南路地铁站附近，想找一个既有倍轻松又有西厅村屋的商场，帮我推荐。",
  "preset.2": "如果不要求两个品牌同时存在，还有没有距离更近的选择？",

  // Tool indicators
  "tool.geocode": "地点定位",
  "tool.nearby": "周边检索",
  "tool.distance": "距离计算",
  "tool.malls": "商场推荐",

  // Status & errors
  "status.error": "⚠️ 请求失败，请检查后端服务是否启动。",
  "status.stopped": "⏹ *已停止生成*",
  "status.backendError": "⚠️ 后端中断请求失败，服务端可能仍在运行。",

  // Debug panel
  "debug.title": "传输流",
  "debug.events": "事件",
  "debug.clear": "清除",
  "debug.empty": "等待 SSE 事件...",
  "debug.emptyHint": "发送消息后，所有原始后端数据将在此处显示。",

  // Conversation sidebar
  "sidebar.label": "会话列表",
  "sidebar.title": "会话",
  "sidebar.newChat": "新建聊天",
  "sidebar.loading": "正在加载会话...",
  "sidebar.loadMore": "加载更多",
  "sidebar.loadingMore": "加载中...",
  "sidebar.emptyTitle": "暂无会话",
  "sidebar.emptyHint": "点击「新建聊天」开始第一段对话。",
  "sidebar.delete": "删除会话",
  "sidebar.deleteConfirm": "确定要永久删除这个会话吗？此操作不可恢复。",

  // Aria labels (button hover/screen-reader)
  "aria.send": "发送",
  "aria.clearHistory": "清除历史",
  "aria.stopGeneration": "停止生成",

  // Language toggle
  "lang.switch": "English",

  // ─── Floating bottom-right action badges ─────────────────────────────
  "floatingLink.deploy": "一键部署",
  "floatingLink.github": "GitHub",
} as const;

export default zh;
