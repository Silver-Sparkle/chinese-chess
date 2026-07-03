const app = getApp()
const { api } = require('../../utils/api')

Page({
  data: {
    roomName: '',
    rooms: [],
    myRoom: null,
    playerId: '',
  },

  onLoad() {
    this.setData({ playerId: app.globalData.playerId })
  },

  onShow() {
    this.refreshRooms()
  },

  onNameInput(e) {
    this.setData({ roomName: e.detail.value })
  },

  // 创建房间
  async createRoom() {
    try {
      const res = await api.createRoom(this.data.roomName || '')
      if (res.success) {
        this.setData({ myRoom: res.room, roomName: '' })
        wx.showToast({ title: '房间创建成功', icon: 'success' })
        this.refreshRooms()
      }
    } catch (e) {
      wx.showToast({ title: '创建失败，检查网络', icon: 'none' })
    }
  },

  // 加入房间
  async joinRoom(e) {
    const roomId = e.currentTarget.dataset.roomId
    try {
      const res = await api.joinRoom(roomId, app.globalData.playerId)
      if (res.success) {
        this.setData({ myRoom: res.room })
        wx.showToast({ title: '加入成功', icon: 'success' })
        this.refreshRooms()
      }
    } catch (e) {
      wx.showToast({ title: '加入失败', icon: 'none' })
    }
  },

  // 离开房间
  async leaveRoom() {
    if (!this.data.myRoom) return
    try {
      await api.leaveRoom(this.data.myRoom.room_id, app.globalData.playerId)
      this.setData({ myRoom: null })
      wx.showToast({ title: '已离开', icon: 'none' })
      this.refreshRooms()
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  // 开始对局
  async startGame() {
    if (!this.data.myRoom) return
    try {
      const res = await api.startGame(this.data.myRoom.room_id, app.globalData.playerId)
      if (res.success) {
        wx.navigateTo({
          url: `/pages/game/game?mode=multiplayer&room_id=${this.data.myRoom.room_id}`
        })
      }
    } catch (e) {
      wx.showToast({ title: '开始失败', icon: 'none' })
    }
  },

  // 刷新列表
  async refreshRooms() {
    try {
      const res = await api.listRooms()
      if (res.success) {
        this.setData({ rooms: res.rooms || [] })
      }
    } catch (e) {
      // 静默失败
      console.log('获取房间列表失败:', e)
    }
  },
})
