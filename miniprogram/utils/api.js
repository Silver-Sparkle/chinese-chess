/**
 * API 请求封装
 *
 * 后端接口:
 *   GET  /api/health          — 健康检查
 *   POST /api/rooms            — 创建房间
 *   GET  /api/rooms            — 房间列表
 *   GET  /api/rooms/{id}       — 房间详情
 *   POST /api/rooms/{id}/join  — 加入房间
 *   POST /api/rooms/{id}/leave — 离开房间
 *   POST /api/rooms/{id}/start — 开始对局
 *   POST /api/ai/start         — 创建AI对局
 *   POST /api/ai/move          — AI对局走棋
 *   GET  /api/ai/game/{id}     — 获取AI对局
 */

const app = getApp()

// 请求封装
function request(method, path, data = {}) {
  return new Promise((resolve, reject) => {
    const url = app.getServerUrl() + path
    wx.request({
      url,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${JSON.stringify(res.data)}`))
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

// API 方法
const api = {
  // 健康检查
  health() {
    return request('GET', '/api/health')
  },

  // ===== 房间 =====

  createRoom(name = '') {
    return request('POST', '/api/rooms', { name })
  },

  listRooms() {
    return request('GET', '/api/rooms')
  },

  getRoom(roomId) {
    return request('GET', `/api/rooms/${roomId}`)
  },

  joinRoom(roomId, playerId) {
    return request('POST', `/api/rooms/${roomId}/join?player_id=${playerId}`)
  },

  leaveRoom(roomId, playerId) {
    return request('POST', `/api/rooms/${roomId}/leave?player_id=${playerId}`)
  },

  startGame(roomId, playerId) {
    return request('POST', `/api/rooms/${roomId}/start?player_id=${playerId}`)
  },

  // ===== AI对局 =====

  startAIGame(params) {
    return request('POST', '/api/ai/start', params)
  },

  aiMove(params) {
    return request('POST', '/api/ai/move', params)
  },

  getAIGame(gameId) {
    return request('GET', `/api/ai/game/${gameId}`)
  },

  // ===== 对局查询 =====

  getGame(roomId) {
    return request('GET', `/api/games/${roomId}`)
  },
}

module.exports = { api, request }
