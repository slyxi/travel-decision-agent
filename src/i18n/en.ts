const en = {
  // Header
  "app.title": "Travel Decision Agent",
  "app.subtitle": "Running on EdgeOne Makers with live Amap map data",

  // Empty state
  "empty.title": "Travel Decision Agent",
  "empty.hint": "I'm a travel decision agent: tell me where you are and which brands you want, and I'll find nearby malls, verify the stores, compare distances and recommend one.",
  "empty.features": "Amap · Store check · Distance compare · Session Memory",

  // Chat input
  "chat.placeholder": "Type a message...  ⏎ Send · Shift+⏎ Newline",
  "chat.hint": "Powered by OpenAI Agents SDK + EdgeOne Makers + Amap",

  // Preset questions
  "preset.1": "I'm near Honglian Nanlu subway station. Find a nearby mall that has both Breo and Xitingcunwu.",
  "preset.2": "If both brands are not required, is there anything closer?",

  // Tool indicators
  "tool.geocode": "Geocode",
  "tool.nearby": "Nearby search",
  "tool.distance": "Distance",
  "tool.malls": "Mall recommend",

  // Status & errors
  "status.error": "Request failed. Please check if the backend service is running.",
  "status.stopped": "⏹ *Generation stopped*",
  "status.backendError": "Backend abort request failed. The server may still be running.",

  // Debug panel
  "debug.title": "Trace",
  "debug.events": "events",
  "debug.clear": "Clear",
  "debug.empty": "Waiting for SSE events...",
  "debug.emptyHint": "After sending a message, all raw backend data will be displayed here.",

  // Conversation sidebar
  "sidebar.label": "Conversation list",
  "sidebar.title": "Chats",
  "sidebar.newChat": "New chat",
  "sidebar.loading": "Loading conversations...",
  "sidebar.loadMore": "Load more",
  "sidebar.loadingMore": "Loading...",
  "sidebar.emptyTitle": "No conversations yet",
  "sidebar.emptyHint": "Click \"New chat\" to start your first conversation.",
  "sidebar.delete": "Delete conversation",
  "sidebar.deleteConfirm": "Permanently delete this conversation? This cannot be undone.",

  // Aria labels (button hover/screen-reader)
  "aria.send": "Send",
  "aria.clearHistory": "Clear history",
  "aria.stopGeneration": "Stop generation",

  // Language toggle
  "lang.switch": "中文",

  // ─── Floating bottom-right action badges ─────────────────────────────
  "floatingLink.deploy": "Deploy",
  "floatingLink.github": "GitHub",
} as const;

export default en;
