const app = getApp()

Page({
  data: {
    aiDepth: 4,       // AI难度
    isConnected: false,
  },

  onLoad() {
    this.checkConnection()
  },

  onShow() {
    this.checkConnection()
  },

  checkConnection() {
    // 检查后端连接
    const url = app.getServerUrl()
    wx.request({
      url: `${url}/api/health`,
      success: () => {
        this.setData({ isConnected: true })
      },
      fail: () => {
        this.setData({ isConnected: false })
      }
    })
  },

  // 设置AI难度
  setDepth(e) {
    const depth = e.currentTarget.dataset.depth
    this.setData({ aiDepth: depth })
  },

  // 开始人机对战
  startAIGame(e) {
    const color = e.currentTarget.dataset.color  // 'red' | 'black'
    const depth = this.data.aiDepth

    wx.navigateTo({
      url: `/pages/game/game?mode=ai&color=${color}&depth=${depth}`
    })
  },

  // 进入联机对战
  goToRoom() {
    wx.switchTab({ url: '/pages/room/room' })
  },

  // 进入历史记录
  goToHistory() {
    wx.switchTab({ url: '/pages/history/history' })
  },
})
