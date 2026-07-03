/**
 * WebSocket / Socket.IO 客户端封装
 *
 * 微信小程序使用 weapp.socket.io 库来连接 Socket.IO 服务端。
 * 如未引入该库，则用原生 WebSocket 降级连接。
 *
 * npm: weapp.socket.io
 * GitHub: https://github.com/weapp-socketio/weapp.socket.io
 */

const app = getApp()

// 事件回调存储
const listeners = {}

class WSClient {
  constructor() {
    this._socket = null
    this._connected = false
    this._url = ''
  }

  /**
   * 连接到 Socket.IO 服务器
   * 需要先安装 weapp.socket.io:
   *   npm install weapp.socket.io
   *   然后在微信开发者工具中构建npm
   */
  connect(url) {
    this._url = url || app.getWsUrl()

    try {
      // 尝试使用 weapp.socket.io
      const io = require('weapp.socket.io')
      this._socket = io(this._url, {
        transports: ['websocket'],
        auth: {
          player_id: app.globalData.playerId,
        },
      })

      this._setupSocketIO()
    } catch (e) {
      // 降级：使用原生 WebSocket（功能有限）
      console.warn('weapp.socket.io 未安装，使用原生 WebSocket')
      this._connectNative()
    }
  }

  _setupSocketIO() {
    const socket = this._socket

    socket.on('connect', () => {
      this._connected = true
      this._emit('connect', {})
    })

    socket.on('disconnect', (reason) => {
      this._connected = false
      this._emit('disconnect', { reason })
    })

    socket.on('connected', (data) => {
      this._emit('connected', data)
    })

    socket.on('error', (data) => {
      this._emit('error', data)
    })

    // 联机对局事件
    socket.on('game:state', (data) => {
      this._emit('game:state', data)
    })

    socket.on('game:start', (data) => {
      this._emit('game:start', data)
    })

    socket.on('game:over', (data) => {
      this._emit('game:over', data)
    })

    socket.on('room:update', (data) => {
      this._emit('room:update', data)
    })

    // AI对局事件
    socket.on('ai:game_started', (data) => {
      this._emit('ai:game_started', data)
    })

    socket.on('ai:move', (data) => {
      this._emit('ai:move', data)
    })

    socket.on('ai:move_accepted', (data) => {
      this._emit('ai:move_accepted', data)
    })
  }

  _connectNative() {
    const socket = wx.connectSocket({
      url: this._url + '/socket.io/?transport=websocket',
    })

    socket.onOpen(() => {
      this._connected = true
      this._emit('connect', {})
    })

    socket.onMessage((msg) => {
      try {
        const data = JSON.parse(msg.data)
        this._emit('message', data)
      } catch (e) {
        console.warn('WebSocket消息解析失败:', msg.data)
      }
    })

    socket.onClose(() => {
      this._connected = false
      this._emit('disconnect', { reason: 'close' })
    })

    socket.onError((err) => {
      this._emit('error', { message: err.errMsg })
    })

    this._socket = socket
  }

  /**
   * 发送事件
   */
  emit(event, data) {
    if (!this._connected) {
      console.warn('WebSocket 未连接')
      return
    }
    if (this._socket && typeof this._socket.emit === 'function') {
      // Socket.IO
      this._socket.emit(event, data)
    } else if (this._socket && this._socket.send) {
      // 原生 WebSocket
      this._socket.send({
        data: JSON.stringify([event, data]),
      })
    }
  }

  /**
   * 加入房间
   */
  joinRoom(roomId) {
    this.emit('room_join', { room_id: roomId })
  }

  /**
   * 离开房间
   */
  leaveRoom(roomId) {
    this.emit('room_leave', { room_id: roomId })
  }

  /**
   * 发送走法
   */
  sendMove(data) {
    this.emit('game_move', data)
  }

  /**
   * 注册事件监听
   */
  on(event, callback) {
    if (!listeners[event]) listeners[event] = []
    listeners[event].push(callback)
  }

  /**
   * 移除事件监听
   */
  off(event, callback) {
    if (!listeners[event]) return
    listeners[event] = listeners[event].filter(cb => cb !== callback)
  }

  _emit(event, data) {
    if (listeners[event]) {
      listeners[event].forEach(cb => {
        try { cb(data) } catch (e) { console.error(e) }
      })
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this._socket) {
      if (typeof this._socket.close === 'function') {
        this._socket.close()
      }
    }
    this._connected = false
  }

  get connected() {
    return this._connected
  }
}

// 单例
const wsClient = new WSClient()

module.exports = { wsClient, WSClient }
