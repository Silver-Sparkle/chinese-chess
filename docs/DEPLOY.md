# 中国象棋 — 正式上线部署指南

---

## 总览

上线分两部分：
1. **后端部署** → 微信云托管（Docker 一键部署）
2. **小程序发布** → 微信公众平台提交审核

---

## 一、前置准备

| 事项 | 说明 |
|------|------|
| 微信小程序 AppID | [mp.weixin.qq.com](https://mp.weixin.qq.com) 注册小程序（个人即可） |
| 微信云开发环境 | 小程序后台 → 开发 → 云开发 → 开通云托管 |
| Docker 了解 | 无需精通，云托管会自动构建 |

---

## 二、后端部署到微信云托管

### 2.1 步骤概览

```
本地代码 → 上传 Git → 云托管自动构建 Docker → 生成公网域名
```

### 2.2 详细步骤

**Step 1: 进入云托管控制台**

1. 打开 [微信公众平台](https://mp.weixin.qq.com) → 登录你的小程序
2. 左侧菜单 → **开发** → **云开发** → **云托管**
3. 开通云托管（首次有免费额度）

**Step 2: 新建服务**

1. 点击「新建服务」
2. 服务名称：`chinese-chess`
3. 部署方式：选择「代码仓库」或「本地代码」
4. 公网访问：开启 → 自动分配 `https://xxx.sh.run.tcloudbase.com` 域名
5. 点击「创建」

**Step 3: 上传代码（二选一）**

方式A — 直接上传文件夹：
  1. 把 `backend/` 整个目录打包成 zip
  2. 在云托管控制台 → 版本管理 → 上传代码包

方式B — 用 Git（推荐）：
  1. 在 GitHub/Gitee 创建仓库
  2. 推送代码：
```bash
cd C:\Users\26740\chinese-chess\backend
git init
git add .
git commit -m "中国象棋后端 v1.0"
git remote add origin <你的仓库地址>
git push -u origin main
```
  3. 云托管关联仓库 → 自动构建部署

**Step 4: 构建与部署**

云托管会自动：
1. 检测 `Dockerfile`
2. 构建 Docker 镜像
3. 部署到容器（PORT=80）
4. 生成公网域名 `https://<服务名>-<随机id>.sh.run.tcloudbase.com`

**Step 5: 验证**

浏览器访问：
```
https://<你的云托管域名>/api/health
```
返回 `{"status": "ok", "version": "1.0.0"}` 即成功。

---

## 三、小程序配置与发布

### 3.1 修改服务器地址

1. 打开 `miniprogram\app.js`
2. 修改两行：
```js
serverUrl: 'https://你的服务名-xxx.sh.run.tcloudbase.com',
wsUrl:    'wss://你的服务名-xxx.sh.run.tcloudbase.com',
```

### 3.2 配置小程序 AppID

1. 打开 `miniprogram\project.config.json`
2. 把 `"appid": "YOUR_APPID_HERE"` 改成你的真实 AppID
3. 在 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 开发管理 → 开发设置：
   - 把云托管域名加到 **服务器域名** (request合法域名)
   - 把云托管域名加到 **socket合法域名** (wss://)

### 3.3 用微信开发者工具上传

1. 打开微信开发者工具
2. 导入 `miniprogram\` 目录
3. 填入 AppID
4. 点击菜单栏「上传」→ 填写版本号 `v1.0.0`
5. 上传成功

### 3.4 提交审核

1. 回到 [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 左侧菜单 → **管理** → **版本管理**
3. 在「开发版本」中找到刚上传的版本
4. 点击「提交审核」→ 填写审核信息：

```
功能：中国象棋对弈游戏
类目：游戏-棋牌
备注：支持人机对战和好友联机对弈的中国象棋游戏。
      包含完整的象棋规则、AI引擎、联机对战功能。
```

5. 提交后等待审核（通常 1-3 个工作日）

### 3.5 审核通过后发布

审核通过后 → 点击「发布」→ 用户即可在微信搜索到你的小程序。

---

## 四、成本预估

| 项目 | 费用 |
|------|------|
| 小程序认证 | 个人免费 / 企业 300元/年 |
| 云托管 | 最低配置约 30-50元/月（2核2G），但有免费额度 |
| 云数据库（可选）| 免费额度够用 |
| 域名 | 云托管自带 HTTPS 域名，免费 |

---

## 五、常见问题

### Q: 部署后前端连不上后端？

**检查：**
1. 小程序后台 → 开发管理 → 服务器域名是否配了云托管域名
2. `app.js` 中的 `serverUrl` 是否以 `https://` 开头
3. 云托管服务是否正常运行（状态为「运行中」）

### Q: WebSocket 连不上？

1. 确认 `wsUrl` 是 `wss://` 开头（不是 `ws://`）
2. 小程序后台「socket合法域名」已配置云托管域名
3. 微信开发者工具中，勾选「不校验合法域名」（仅调试用）

### Q: AI 走棋太慢？

云托管最低配可能较慢，可以：
1. 在云托管控制台升级配置（1核→2核）
2. 或者在 `config.py` 环境变量中降低 `AI_MAX_DEPTH=3`

### Q: 怎么让用户登录？

目前是匿名方式。如果要真实的用户系统：
1. `wx.login()` 获取 code
2. 后端用 code 调微信接口换取 openid
3. 用 openid 作为用户标识

---

## 六、项目文件对应表

```
本地路径                            云端/微信
───────────────────────────────────────────────────
backend/              ──上传──▶   微信云托管（Docker容器）
  ├── Dockerfile                  云托管自动构建
  ├── app.py                      启动: uvicorn
  └── ...                         生成域名 *.sh.run.tcloudbase.com

miniprogram/          ──上传──▶   微信小程序平台
  ├── app.js                      需改 serverUrl
  ├── project.config.json         需改 appid
  └── ...                         审核通过后发布
```
