# Release Guide

本文档介绍如何发布 AIMD Studio 扩展到 VS Code Marketplace 和 Open VSX。

## 自动发布（推荐）

创建 GitHub Release 后会自动触发发布流程。

### 步骤

1. **更新版本号**
   ```bash
   # 编辑 package.json 中的 version 字段
   # 例如：0.3.1 -> 0.3.2
   ```

2. **更新文档**
   - `CHANGELOG.md` - 添加新版本的更改说明
   - `README.md` - 更新 Release Notes 部分

3. **提交并推送**
   ```bash
   git add package.json CHANGELOG.md README.md
   git commit -m "chore: Bump version to x.x.x"
   git push origin main
   ```

4. **创建 Tag 并推送**
   ```bash
   git tag vX.X.X
   git push origin vX.X.X
   ```

5. **创建 GitHub Release**
   - 访问 https://github.com/xiayh17/aimd-studio-extension/releases/new
   - 选择刚创建的 tag
   - 填写 Release notes
   - 点击 **Publish release**

6. **等待自动发布**
   - GitHub Actions 会自动构建所有平台的二进制
   - 自动发布到 VS Code Marketplace
   - 自动发布到 Open VSX

### 查看发布状态

- **Actions**: https://github.com/xiayh17/aimd-studio-extension/actions
- **VS Code Marketplace**: https://marketplace.visualstudio.com/items?itemName=yonghe.aimd-studio
- **Open VSX**: https://open-vsx.org/extension/yonghe/aimd-studio

---

## 手动发布

如果自动发布失败，可以手动发布。

### VS Code Marketplace

```bash
# 需要设置 VSCE_PAT 环境变量
npx vsce publish -p $VSCE_PAT
```

### Open VSX

```bash
# 需要设置 OVSX_PAT 环境变量
npx ovsx publish -p $OVSX_PAT
```

---

## 首次设置

### 获取 Token

1. **VSCE_PAT** (VS Code Marketplace)
   - 访问 https://dev.azure.com/
   - 创建 Personal Access Token
   - 权限需要 `Marketplace > Manage`

2. **OVSX_PAT** (Open VSX)
   - 访问 https://open-vsx.org/user-settings/tokens
   - 创建 Access Token

### 配置 GitHub Secrets

在仓库设置中添加：
- `VSCE_PAT` - VS Code Marketplace token
- `OVSX_PAT` - Open VSX token

### 创建 Open VSX Namespace（一次性）

```bash
npx ovsx create-namespace yonghe -p YOUR_OVSX_PAT
```

---

## 发布内容

发布包含：
- 扩展核心代码 (经过 `esbuild` 打包，包含所有运行时依赖)
- 多平台 Python 后端二进制
  - `aimd-server-win32-x64.exe`
  - `aimd-server-darwin-arm64`
  - `aimd-server-darwin-x64`
  - `aimd-server-linux-x64`
