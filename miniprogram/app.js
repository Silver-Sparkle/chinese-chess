/**
 * 中国象棋 - 微信小程序
 *
 * 上线前需修改:
 *   1. serverUrl — 改为云托管域名
 *   2. wsUrl     — 改为云托管 WebSocket 域名
 */

App({
  globalData: {
    // ==========================================
    // ★ 上线前务必修改为微信云托管域名 ★
    // ==========================================
    serverUrl: 'https://your-service-xxxx.sh.run.tcloudbase.com',
    wsUrl: 'wss://your-service-xxxx.sh.run.tcloudbase.com',

    playerId: '',
    playerName: '棋友',
    isConnected: false,
  },

  onLaunch() {
    // 登录获取 openid
    wx.login({
      success: (res) => {
        if (res.code) {
          // 可以用 code 调用云函数换取 openid
          this.globalData.playerId = 'user_' + Date.now().toString(36)
        }
      }
    })

    const sysInfo = wx.getSystemInfoSync()
    this.globalData.systemInfo = sysInfo
  },

  getServerUrl() {
    return this.globalData.serverUrl
  },

  getWsUrl() {
    return this.globalData.wsUrl
  },
})
