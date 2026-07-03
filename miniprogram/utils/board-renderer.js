/**
 * 棋盘 Canvas 渲染工具
 *
 * 提供棋盘绘制、棋子渲染、触摸坐标转换等功能。
 * 供 game.js 使用。
 */

// 棋盘常量
const ROWS = 10
const COLS = 9

/**
 * 绘制完整棋盘（网格线、九宫斜线、楚河汉界）
 */
function drawBoard(ctx, w, h) {
  const padding = 30
  const cellW = (w - padding * 2) / 8
  const cellH = (h - padding * 2) / 9

  // 棋盘背景
  ctx.fillStyle = '#DEB887'
  ctx.fillRect(0, 0, w, h)

  // 网格线颜色
  ctx.strokeStyle = '#5D3A1A'
  ctx.lineWidth = 1.5

  // 横线 (10条)
  for (let row = 0; row < ROWS; row++) {
    const y = padding + row * cellH
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(w - padding, y)
    ctx.stroke()
  }

  // 竖线 (9条，河界处断开)
  for (let col = 0; col < COLS; col++) {
    const x = padding + col * cellW
    // 上半 (row 0-4)
    ctx.beginPath()
    ctx.moveTo(x, padding)
    ctx.lineTo(x, padding + 4 * cellH)
    ctx.stroke()
    // 下半 (row 5-9)
    ctx.beginPath()
    ctx.moveTo(x, padding + 5 * cellH)
    ctx.lineTo(x, h - padding)
    ctx.stroke()

    // 第0列和第8列的竖线贯穿（左右边界）
    if (col === 0 || col === 8) {
      ctx.beginPath()
      ctx.moveTo(x, padding)
      ctx.lineTo(x, h - padding)
      ctx.stroke()
    }
  }

  // 九宫斜线
  drawPalaceLines(ctx, padding, cellW, cellH, 0, 3)   // 红方 (top)
  drawPalaceLines(ctx, padding, cellW, cellH, 7, 3)   // 黑方 (bottom)

  // 楚河汉界文字
  ctx.font = `bold ${cellH * 0.4}px "KaiTi", "STKaiti", serif`
  ctx.fillStyle = '#5D3A1A'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const riverY = padding + 4.5 * cellH
  ctx.fillText('楚    河', padding + 2 * cellW, riverY)
  ctx.fillText('汉    界', padding + 6 * cellW, riverY)

  return { padding, cellW, cellH }
}

/**
 * 绘制九宫斜线
 */
function drawPalaceLines(ctx, padding, cellW, cellH, startRow, startCol) {
  const x1 = padding + startCol * cellW
  const y1 = padding + startRow * cellH
  const x2 = padding + (startCol + 2) * cellW
  const y2 = padding + (startRow + 2) * cellH

  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(x2, y1)
  ctx.lineTo(x1, y2)
  ctx.stroke()
}

/**
 * 绘制棋子
 * @param {CanvasContext} ctx
 * @param {number} w - canvas width
 * @param {number} h - canvas height
 * @param {Array} pieces - [{row, col, color, type, name}]
 * @param {Object} boardParams - {padding, cellW, cellH}
 * @param {Object|null} selected - {row, col} 选中的棋子
 */
function drawPieces(ctx, w, h, pieces, boardParams, selected) {
  const { padding, cellW, cellH } = boardParams
  const radius = Math.min(cellW, cellH) * 0.42

  for (const piece of pieces) {
    const x = padding + piece.col * cellW
    const y = padding + piece.row * cellH

    // 选中高亮光环
    if (selected && selected.row === piece.row && selected.col === piece.col) {
      ctx.beginPath()
      ctx.arc(x, y, radius + 6, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255, 215, 0, 0.6)'
      ctx.fill()
    }

    // 棋子阴影
    ctx.beginPath()
    ctx.arc(x + 2, y + 2, radius, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.15)'
    ctx.fill()

    // 棋子底色
    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    const gradient = ctx.createRadialGradient(x - 3, y - 3, radius * 0.1, x, y, radius)
    gradient.addColorStop(0, '#FFF8DC')
    gradient.addColorStop(1, '#E8D5A3')
    ctx.fillStyle = gradient
    ctx.fill()

    // 棋子边框
    ctx.strokeStyle = piece.color === 'red' ? '#B22222' : '#1a1a2e'
    ctx.lineWidth = 2.5
    ctx.stroke()

    // 内圈
    ctx.beginPath()
    ctx.arc(x, y, radius - 5, 0, Math.PI * 2)
    ctx.strokeStyle = piece.color === 'red' ? '#c0392b' : '#2c3e50'
    ctx.lineWidth = 1
    ctx.stroke()

    // 棋子文字
    const fontSize = radius * 1.1
    ctx.font = `bold ${fontSize}px "KaiTi", "STKaiti", "PingFang SC", "Microsoft YaHei", sans-serif`
    ctx.fillStyle = piece.color === 'red' ? '#B22222' : '#1a1a2e'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(piece.name, x, y + 1)
  }
}

/**
 * 绘制可走位置高亮
 * @param {CanvasContext} ctx
 * @param {Array} legalMoves - [{row, col}]
 * @param {Array} pieces - 用于判断目标位置是否有可吃的子
 * @param {Object} boardParams
 */
function drawHighlights(ctx, w, h, legalMoves, pieces, boardParams) {
  if (!legalMoves || !legalMoves.length) return
  const { padding, cellW, cellH } = boardParams
  const dotRadius = Math.min(cellW, cellH) * 0.16

  for (const move of legalMoves) {
    const x = padding + move.col * cellW
    const y = padding + move.row * cellH
    const hasCapture = pieces.some(p => p.row === move.row && p.col === move.col)

    ctx.beginPath()
    ctx.arc(x, y, dotRadius, 0, Math.PI * 2)
    if (hasCapture) {
      // 可吃子：红色半透明圆环
      ctx.strokeStyle = 'rgba(220, 50, 50, 0.7)'
      ctx.lineWidth = 3
      ctx.stroke()
    } else {
      // 可移动：绿色半透明圆点
      ctx.fillStyle = 'rgba(50, 180, 80, 0.5)'
      ctx.fill()
    }
  }
}

/**
 * 将触摸坐标转换为最近的棋盘交叉点
 * @param {number} touchX
 * @param {number} touchY
 * @param {Object} boardParams
 * @returns {{row: number, col: number}|null}
 */
function getIntersection(touchX, touchY, boardParams) {
  const { padding, cellW, cellH } = boardParams

  const col = Math.round((touchX - padding) / cellW)
  const row = Math.round((touchY - padding) / cellH)

  if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return null

  const cx = padding + col * cellW
  const cy = padding + row * cellH
  const dist = Math.sqrt((touchX - cx) ** 2 + (touchY - cy) ** 2)
  const threshold = Math.min(cellW, cellH) * 0.45

  if (dist > threshold) return null
  return { row, col, colChar: String.fromCharCode(65 + col) }
}

module.exports = {
  drawBoard,
  drawPieces,
  drawHighlights,
  getIntersection,
  ROWS,
  COLS,
}
