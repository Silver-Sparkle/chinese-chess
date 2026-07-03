Page({
  data: {
    stats: {
      total: 0,
      wins: 0,
      losses: 0,
      draws: 0,
    },
    records: [],
  },

  onShow() {
    this.loadRecords()
  },

  loadRecords() {
    // 从本地存储加载对局记录
    try {
      const records = wx.getStorageSync('chess_records') || []
      const stats = this.calcStats(records)
      this.setData({
        records: records.slice(0, 50).map(r => this.formatRecord(r)),
        stats,
      })
    } catch (e) {
      console.error('加载记录失败:', e)
    }
  },

  calcStats(records) {
    let wins = 0, losses = 0, draws = 0
    for (const r of records) {
      if (r.result === 'win') wins++
      else if (r.result === 'lose') losses++
      else draws++
    }
    return {
      total: records.length,
      wins,
      losses,
      draws,
    }
  },

  formatRecord(r) {
    const resultMap = {
      win: { text: '胜', cls: 'win' },
      lose: { text: '负', cls: 'lose' },
      draw: { text: '和', cls: 'draw' },
    }
    const res = resultMap[r.result] || { text: '?', cls: '' }
    return {
      ...r,
      result_text: res.text,
      result_class: res.cls,
      date: r.date ? r.date.slice(0, 10) : '',
    }
  },
})
