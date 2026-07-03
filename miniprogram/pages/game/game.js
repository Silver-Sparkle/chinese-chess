/**
 * 对局页面 — 棋盘渲染 + 交互逻辑
 */
import { drawBoard, drawPieces, drawHighlights, getIntersection } from '../../utils/board-renderer'
import { api } from '../../utils/api'

const app = getApp()

// 棋盘常量
const ROWS = 10
const COLS = 9

Page({
  data: {
    // 游戏模式
    mode: 'ai',       // 'ai' | 'multiplayer'
    playerColor: 'red',
    aiDepth: 4,

    // 显示
    opponentName: 'AI',
    opponentLabel: '',
    opponentColor: 'black',
    playerName: '我',
    playerLabel: '',
    statusText: '对局中',
    moveLog: [],
    canUndo: false,

    // 结果弹窗
    showResult: false,
    resultIcon: '',
    resultTitle: '',
    resultReason: '',
  },

  // ---- 内部状态 ----
  _pieces: [],        // [{row, col, color, type, name}]
  _selectedPiece: null,  // {row, col}
  _legalMoves: [],     // [{row, col}]
  _currentTurn: 'red',
  _gameId: null,
  _moveHistory: [],
  _gameOver: false,
  _isAIThinking: false,
  _canvas: null,
  _ctx: null,
  _canvasWidth: 0,
  _canvasHeight: 0,
  _dpr: 1,

  // ==================== 生命周期 ====================

  onLoad(options) {
    const { mode, color, depth } = options
    this.setData({
      mode: mode || 'ai',
      playerColor: color || 'red',
      aiDepth: parseInt(depth) || 4,
    })

    if (color === 'black') {
      this.setData({
        opponentName: 'AI (红)',
        opponentColor: 'red',
        playerName: '我 (黑)',
        playerLabel: '黑方',
        opponentLabel: '红方',
      })
    } else {
      this.setData({
        opponentName: 'AI (黑)',
        opponentColor: 'black',
        playerName: '我 (红)',
        playerLabel: '红方',
        opponentLabel: '黑方',
      })
    }
  },

  onReady() {
    this._initCanvas()
  },

  onShow() {
    if (this._canvas) {
      this._render()
    }
  },

  // ==================== Canvas 初始化 ====================

  _initCanvas() {
    const query = wx.createSelectorQuery()
    query.select('#chessCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) {
          console.error('Canvas not found, retrying...')
          setTimeout(() => this._initCanvas(), 300)
          return
        }

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getSystemInfoSync().pixelRatio

        this._canvasWidth = res[0].width
        this._canvasHeight = res[0].height
        this._dpr = dpr

        canvas.width = this._canvasWidth * dpr
        canvas.height = this._canvasHeight * dpr
        ctx.scale(dpr, dpr)

        this._canvas = canvas
        this._ctx = ctx

        // 初始化棋盘
        this._initGame()
      })
  },

  // ==================== 游戏初始化 ====================

  async _initGame() {
    if (this.data.mode === 'ai') {
      await this._startAIGame()
    } else {
      this._initLocalGame()
    }
    this._render()
  },

  async _startAIGame() {
    try {
      const res = await api.startAIGame({
        player_color: this.data.playerColor,
        ai_depth: this.data.aiDepth,
        player_id: app.globalData.playerId,
      })

      if (res.success && res.game) {
        this._gameId = res.game.game_id
        this._loadBoardState(res.game)

        // AI先手已走
        if (res.ai_move) {
          this._loadBoardState(res.game)
          this._addMoveLog(res.ai_move)
        }
      }
    } catch (e) {
      console.error('启动AI对局失败:', e)
      // 离线模式：本地棋盘
      this._initLocalGame()
    }
  },

  _initLocalGame() {
    // 本地初始布局（离线模式）
    this._pieces = this._getInitialPieces()
    this._currentTurn = 'red'
    this._gameId = 'local_' + Date.now()
  },

  _getInitialPieces() {
    const pieces = []
    // 红方
    pieces.push(
      { row: 0, col: 0, color: 'red', type: 'rook', name: '車' },
      { row: 0, col: 1, color: 'red', type: 'horse', name: '馬' },
      { row: 0, col: 2, color: 'red', type: 'elephant', name: '相' },
      { row: 0, col: 3, color: 'red', type: 'advisor', name: '仕' },
      { row: 0, col: 4, color: 'red', type: 'king', name: '帅' },
      { row: 0, col: 5, color: 'red', type: 'advisor', name: '仕' },
      { row: 0, col: 6, color: 'red', type: 'elephant', name: '相' },
      { row: 0, col: 7, color: 'red', type: 'horse', name: '馬' },
      { row: 0, col: 8, color: 'red', type: 'rook', name: '車' },
      { row: 2, col: 1, color: 'red', type: 'cannon', name: '炮' },
      { row: 2, col: 7, color: 'red', type: 'cannon', name: '炮' },
      { row: 3, col: 0, color: 'red', type: 'pawn', name: '兵' },
      { row: 3, col: 2, color: 'red', type: 'pawn', name: '兵' },
      { row: 3, col: 4, color: 'red', type: 'pawn', name: '兵' },
      { row: 3, col: 6, color: 'red', type: 'pawn', name: '兵' },
      { row: 3, col: 8, color: 'red', type: 'pawn', name: '兵' },
    )
    // 黑方
    pieces.push(
      { row: 9, col: 0, color: 'black', type: 'rook', name: '车' },
      { row: 9, col: 1, color: 'black', type: 'horse', name: '马' },
      { row: 9, col: 2, color: 'black', type: 'elephant', name: '象' },
      { row: 9, col: 3, color: 'black', type: 'advisor', name: '士' },
      { row: 9, col: 4, color: 'black', type: 'king', name: '将' },
      { row: 9, col: 5, color: 'black', type: 'advisor', name: '士' },
      { row: 9, col: 6, color: 'black', type: 'elephant', name: '象' },
      { row: 9, col: 7, color: 'black', type: 'horse', name: '马' },
      { row: 9, col: 8, color: 'black', type: 'rook', name: '车' },
      { row: 7, col: 1, color: 'black', type: 'cannon', name: '砲' },
      { row: 7, col: 7, color: 'black', type: 'cannon', name: '砲' },
      { row: 6, col: 0, color: 'black', type: 'pawn', name: '卒' },
      { row: 6, col: 2, color: 'black', type: 'pawn', name: '卒' },
      { row: 6, col: 4, color: 'black', type: 'pawn', name: '卒' },
      { row: 6, col: 6, color: 'black', type: 'pawn', name: '卒' },
      { row: 6, col: 8, color: 'black', type: 'pawn', name: '卒' },
    )
    return pieces
  },

  _loadBoardState(gameState) {
    if (!gameState || !gameState.pieces) return
    this._pieces = gameState.pieces.map(p => ({
      row: p.row,
      col: p.col,
      color: p.color,
      type: p.type,
      name: p.name,
    }))
    this._currentTurn = gameState.current_turn || 'red'
    this._gameOver = gameState.state === 'finished'

    const turnMap = { red: '红方走棋', black: '黑方走棋' }
    this.setData({ statusText: turnMap[this._currentTurn] || '对局中' })
  },

  // ==================== Canvas 渲染 ====================

  _render() {
    if (!this._ctx || !this._canvasWidth || !this._canvasHeight) return

    const ctx = this._ctx
    const w = this._canvasWidth
    const h = this._canvasHeight

    // 清空
    ctx.clearRect(0, 0, w, h)

    // 绘制棋盘
    this._drawBoard(ctx, w, h)

    // 绘制高亮
    this._drawHighlights(ctx, w, h)

    // 绘制棋子
    this._drawPieces(ctx, w, h)
  },

  _drawBoard(ctx, w, h) {
    const padding = 30
    const cellW = (w - padding * 2) / 8
    const cellH = (h - padding * 2) / 9

    ctx.strokeStyle = '#5D3A1A'
    ctx.lineWidth = 1.5

    // 横线
    for (let row = 0; row < ROWS; row++) {
      const y = padding + row * cellH
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(w - padding, y)
      ctx.stroke()
    }

    // 竖线（注意河界处断开）
    for (let col = 0; col < COLS; col++) {
      const x = padding + col * cellW
      // 上半部分
      ctx.beginPath()
      ctx.moveTo(x, padding)
      ctx.lineTo(x, padding + 4 * cellH)
      ctx.stroke()
      // 下半部分
      ctx.beginPath()
      ctx.moveTo(x, padding + 5 * cellH)
      ctx.lineTo(x, h - padding)
      ctx.stroke()
    }

    // 左右边界竖线贯穿
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, h - padding)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(w - padding, padding)
    ctx.lineTo(w - padding, h - padding)
    ctx.stroke()

    // 九宫斜线
    const drawPalace = (startRow, startCol) => {
      const x = padding + startCol * cellW
      const y = padding + startRow * cellH
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x + 2 * cellW, y + 2 * cellH)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(x + 2 * cellW, y)
      ctx.lineTo(x, y + 2 * cellH)
      ctx.stroke()
    }
    drawPalace(0, 3)  // 红方九宫
    drawPalace(7, 3)  // 黑方九宫

    // 楚河汉界
    const riverY = padding + 4.5 * cellH
    ctx.font = `${cellH * 0.45}px serif`
    ctx.fillStyle = '#5D3A1A'
    ctx.textAlign = 'center'
    ctx.fillText('楚  河', padding + 1.5 * cellW, riverY - 4)
    ctx.fillText('汉  界', padding + 6.5 * cellW, riverY - 4)

    // 存储坐标参数
    this._boardParams = { padding, cellW, cellH }
  },

  _drawPieces(ctx, w, h) {
    const { padding, cellW, cellH } = this._boardParams
    const radius = Math.min(cellW, cellH) * 0.42

    for (const piece of this._pieces) {
      const x = padding + piece.col * cellW
      const y = padding + piece.row * cellH

      // 选中高亮
      if (this._selectedPiece &&
          this._selectedPiece.row === piece.row &&
          this._selectedPiece.col === piece.col) {
        ctx.beginPath()
        ctx.arc(x, y, radius + 6, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(255, 215, 0, 0.5)'
        ctx.fill()
      }

      // 棋子外圈
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      ctx.fillStyle = '#FAEBD7'
      ctx.fill()
      ctx.strokeStyle = piece.color === 'red' ? '#c0392b' : '#2c3e50'
      ctx.lineWidth = 2.5
      ctx.stroke()

      // 内圈
      ctx.beginPath()
      ctx.arc(x, y, radius - 4, 0, Math.PI * 2)
      ctx.strokeStyle = piece.color === 'red' ? '#c0392b' : '#2c3e50'
      ctx.lineWidth = 1
      ctx.stroke()

      // 文字
      ctx.font = `bold ${radius * 1.1}px "PingFang SC", "Microsoft YaHei", sans-serif`
      ctx.fillStyle = piece.color === 'red' ? '#c0392b' : '#2c3e50'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(piece.name, x, y + 1)
    }
  },

  _drawHighlights(ctx, w, h) {
    if (!this._legalMoves.length) return
    const { padding, cellW, cellH } = this._boardParams
    const radius = Math.min(cellW, cellH) * 0.15

    for (const move of this._legalMoves) {
      const x = padding + move.col * cellW
      const y = padding + move.row * cellH

      // 检查该位置是否有可吃的棋子
      const hasCapture = this._pieces.some(p => p.row === move.row && p.col === move.col)

      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      if (hasCapture) {
        ctx.fillStyle = 'rgba(231, 76, 60, 0.4)'
      } else {
        ctx.fillStyle = 'rgba(39, 174, 96, 0.4)'
      }
      ctx.fill()
    }
  },

  // ==================== 触摸交互 ====================

  onTouchStart(e) {
    if (this._gameOver || this._isAIThinking) return
    if (this.data.mode === 'ai' && this._currentTurn !== this.data.playerColor) return

    const touch = e.touches[0]
    const pos = this._getBoardPos(touch.x, touch.y)
    if (!pos) return

    const { row, col } = pos

    // 如果已选中棋子，再次点击尝试走棋
    if (this._selectedPiece) {
      const legalTarget = this._legalMoves.find(m => m.row === row && m.col === col)
      if (legalTarget) {
        this._executeMove(this._selectedPiece.row, this._selectedPiece.col, row, col)
        return
      }
      // 点击自己的其他棋子则切换选中
      const piece = this._pieces.find(p => p.row === row && p.col === col)
      if (piece && piece.color === this._currentTurn) {
        this._selectPiece(row, col)
        return
      }
      // 否则取消选中
      this._clearSelection()
      return
    }

    // 选中棋子
    const piece = this._pieces.find(p => p.row === row && p.col === col)
    if (piece && piece.color === this._currentTurn) {
      this._selectPiece(row, col)
    }
  },

  onTouchMove(e) {
    // 拖拽支持（简化：不做拖拽动画）
  },

  onTouchEnd(e) {
    // 处理在 touchstart 中
  },

  _getBoardPos(touchX, touchY) {
    if (!this._boardParams) return null
    const { padding, cellW, cellH } = this._boardParams

    // touch坐标需要根据canvas在屏幕上的实际位置和缩放来转换
    // 这里简化处理：直接使用canvas的坐标
    const x = touchX
    const y = touchY

    const col = Math.round((x - padding) / cellW)
    const row = Math.round((y - padding) / cellH)

    // 检查是否在棋盘范围内
    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return null

    // 检查是否足够接近交叉点
    const cx = padding + col * cellW
    const cy = padding + row * cellH
    const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    const threshold = Math.min(cellW, cellH) * 0.45
    if (dist > threshold) return null

    return { row, col }
  },

  _selectPiece(row, col) {
    this._selectedPiece = { row, col }
    // 生成合法走法（这里简化：显示可达目标）
    this._legalMoves = this._getPseudoLegalMoves(row, col)
    this._render()
  },

  _clearSelection() {
    this._selectedPiece = null
    this._legalMoves = []
    this._render()
  },

  // ==================== 走法逻辑（简化本地版） ====================

  _getPseudoLegalMoves(row, col) {
    // 简化的伪合法走法生成，仅用于前端高亮显示
    // 完整的合法性验证由后端完成
    const piece = this._pieces.find(p => p.row === row && p.col === col)
    if (!piece) return []

    const moves = []
    const type = piece.type
    const color = piece.color
    const forward = color === 'red' ? 1 : -1
    const ownHalf = (r) => color === 'red' ? r <= 4 : r >= 5
    const crossedRiver = (r) => color === 'red' ? r >= 5 : r <= 4
    const inPalace = (r, c) => {
      if (color === 'red') return r >= 0 && r <= 2 && c >= 3 && c <= 5
      return r >= 7 && r <= 9 && c >= 3 && c <= 5
    }

    const canMoveTo = (r, c) => {
      if (r < 0 || r > 9 || c < 0 || c > 8) return false
      const target = this._pieces.find(p => p.row === r && p.col === c)
      return !target || target.color !== color
    }

    const addLine = (dr, dc) => {
      let r = row + dr, c = col + dc
      while (r >= 0 && r <= 9 && c >= 0 && c <= 8) {
        const target = this._pieces.find(p => p.row === r && p.col === c)
        if (target) {
          if (target.color !== color) moves.push({ row: r, col: c })
          break
        }
        moves.push({ row: r, col: c })
        r += dr; c += dc
      }
    }

    switch (type) {
      case 'king':
        for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {
          const r = row + dr, c = col + dc
          if (inPalace(r, c) && canMoveTo(r, c)) moves.push({ row: r, col: c })
        }
        break
      case 'advisor':
        for (const [dr, dc] of [[-1,-1],[-1,1],[1,-1],[1,1]]) {
          const r = row + dr, c = col + dc
          if (inPalace(r, c) && canMoveTo(r, c)) moves.push({ row: r, col: c })
        }
        break
      case 'elephant':
        for (const [dr, dc, er, ec] of [[-2,-2,-1,-1],[-2,2,-1,1],[2,-2,1,-1],[2,2,1,1]]) {
          const r = row + dr, c = col + dc
          const eyeR = row + er, eyeC = col + ec
          if (ownHalf(r) && !this._pieces.find(p => p.row === eyeR && p.col === eyeC) && canMoveTo(r, c)) {
            moves.push({ row: r, col: c })
          }
        }
        break
      case 'horse':
        for (const [dr, dc, lr, lc] of [
          [-2,-1,-1,0],[-2,1,-1,0],[-1,-2,0,-1],[-1,2,0,1],
          [1,-2,0,-1],[1,2,0,1],[2,-1,1,0],[2,1,1,0]
        ]) {
          const legR = row + lr, legC = col + lc
          if (!this._pieces.find(p => p.row === legR && p.col === legC)) {
            const r = row + dr, c = col + dc
            if (canMoveTo(r, c)) moves.push({ row: r, col: c })
          }
        }
        break
      case 'rook':
        for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) addLine(dr, dc)
        break
      case 'cannon':
        for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {
          let r = row + dr, c = col + dc, hasScreen = false
          while (r >= 0 && r <= 9 && c >= 0 && c <= 8) {
            const target = this._pieces.find(p => p.row === r && p.col === c)
            if (!hasScreen) {
              if (target) hasScreen = true
              else moves.push({ row: r, col: c })
            } else {
              if (target && target.color !== color) { moves.push({ row: r, col: c }); break }
              if (target) break
            }
            r += dr; c += dc
          }
        }
        break
      case 'pawn':
        const fr = row + forward
        if (canMoveTo(fr, col)) moves.push({ row: fr, col })
        if (crossedRiver(row)) {
          for (const dc of [-1, 1]) {
            if (canMoveTo(row, col + dc)) moves.push({ row, col: col + dc })
          }
        }
        break
    }
    return moves
  },

  // ==================== 走法执行 ====================

  async _executeMove(fromRow, fromCol, toRow, toCol) {
    const piece = this._pieces.find(p => p.row === fromRow && p.col === fromCol)
    if (!piece) return

    const captured = this._pieces.find(p => p.row === toRow && p.col === toCol)

    // 本地更新
    if (captured) {
      this._pieces = this._pieces.filter(p => p !== captured)
    }
    piece.row = toRow
    piece.col = toCol

    // 切换回合
    this._currentTurn = this._currentTurn === 'red' ? 'black' : 'red'

    // 记录走法
    const moveDesc = `${piece.name}(${fromCol},${fromRow})→(${toCol},${toRow})${captured ? '吃' + captured.name : ''}`
    this._addMoveLog({ piece: piece.name, captured: captured ? captured.name : null })

    this._clearSelection()
    this._render()

    // AI模式：发送到后端
    if (this.data.mode === 'ai' && !this._gameOver) {
      try {
        this._isAIThinking = true
        this.setData({ statusText: 'AI思考中...' })

        const res = await api.aiMove({
          game_id: this._gameId,
          from_row: fromRow,
          from_col: fromCol,
          to_row: toRow,
          to_col: toCol,
          player_id: app.globalData.playerId,
        })

        if (res.success) {
          this._loadBoardState(res.game_state)
          if (res.ai_move) {
            this._applyAIMove(res.ai_move)
            this._addMoveLog(res.ai_move)
          }
          if (res.game_state && res.game_state.state === 'finished') {
            this._onGameOver(res.game_state.result || res.game_state)
          }
        }
      } catch (e) {
        console.error('AI走法请求失败:', e)
        // 离线模式：简单AI（随机走法）
        this._localAIMove()
      } finally {
        this._isAIThinking = false
        this._render()
      }
    }

    // 本地模式：检查将死
    if (this.data.mode !== 'ai') {
      this._checkLocalGameOver()
    }
  },

  _applyAIMove(moveData) {
    const [fr, fc] = moveData.from
    const [tr, tc] = moveData.to

    const piece = this._pieces.find(p => p.row === fr && p.col === fc)
    if (!piece) return

    const captured = this._pieces.find(p => p.row === tr && p.col === tc)
    if (captured) this._pieces = this._pieces.filter(p => p !== captured)

    piece.row = tr
    piece.col = tc
    this._currentTurn = this._currentTurn === 'red' ? 'black' : 'red'
  },

  _localAIMove() {
    // 简单的随机AI走法（离线后备）
    const aiColor = this._currentTurn
    const aiPieces = this._pieces.filter(p => p.color === aiColor)
    if (!aiPieces.length) return

    // 随机选一个棋子
    const piece = aiPieces[Math.floor(Math.random() * aiPieces.length)]
    const moves = this._getPseudoLegalMoves(piece.row, piece.col)
    if (!moves.length) return

    const move = moves[Math.floor(Math.random() * moves.length)]
    this._executeMove(piece.row, piece.col, move.row, move.col)
  },

  _addMoveLog(moveData) {
    const pieceName = moveData.piece || ''
    const capturedName = moveData.captured || ''
    let desc = ''
    if (capturedName) {
      desc = pieceName + '吃' + capturedName
    } else {
      desc = pieceName
    }
    const log = [...this.data.moveLog, desc]
    if (log.length > 50) log.shift()
    this.setData({
      moveLog: log,
      canUndo: this._currentTurn === this.data.playerColor,
    })
  },

  _onGameOver(result) {
    this._gameOver = true
    const winStatus = result.status || result
    const reason = result.reason || ''

    let icon, title
    if (winStatus === 'red_wins') {
      icon = '🏆'; title = this.data.playerColor === 'red' ? '你赢了！' : '你输了'
    } else if (winStatus === 'black_wins') {
      icon = '🏆'; title = this.data.playerColor === 'black' ? '你赢了！' : '你输了'
    } else {
      icon = '🤝'; title = '和棋'
    }

    this.setData({
      showResult: true,
      resultIcon: icon,
      resultTitle: title,
      resultReason: reason,
      statusText: '对局结束',
    })
  },

  _checkLocalGameOver() {
    // 简化终局判定
    const currentColor = this._currentTurn
    const hasKing = this._pieces.some(p => p.color === currentColor && p.type === 'king')
    if (!hasKing) {
      this._onGameOver({
        status: currentColor === 'red' ? 'black_wins' : 'red_wins',
        reason: '将/帅被吃',
      })
    }
  },

  // ==================== 按钮操作 ====================

  undoMove() {
    wx.showToast({ title: '暂不支持', icon: 'none' })
  },

  newGame() {
    this._pieces = this._getInitialPieces()
    this._currentTurn = 'red'
    this._selectedPiece = null
    this._legalMoves = []
    this._gameOver = false
    this._isAIThinking = false
    this._moveHistory = []
    this.setData({
      moveLog: [],
      canUndo: false,
      showResult: false,
      statusText: '对局中',
    })
    this._render()

    if (this.data.mode === 'ai') {
      // 重新开始AI对局
      this._startAIGame().then(() => this._render())
    }
  },

  surrender() {
    wx.showModal({
      title: '确认认输',
      content: '确定要认输吗？',
      success: (res) => {
        if (res.confirm) {
          const loserColor = this.data.playerColor
          this._onGameOver({
            status: loserColor === 'red' ? 'black_wins' : 'red_wins',
            reason: '认输',
          })
        }
      }
    })
  },

  backToHome() {
    wx.navigateBack()
  },
})
