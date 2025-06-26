# 📚 ZTZT项目 Git操作指南 (简化版)

> **文档版本**: v2.0  
> **更新日期**: 2025年6月26日  
> **适用项目**: ZTZT AI中台解决方案  
> **面向对象**: 开发人员、运维人员、项目维护者

---

## 📋 目录

1. [标准Git工作流程](#-标准git工作流程)
2. [命名规范](#-命名规范)
3. [冲突解决](#-冲突解决)
4. [快速参考](#-快速参考)

---

## 🚀 标准Git工作流程

### 完整开发流程示例

```bash
# === 1. 准备工作 ===
# 切换到主开发分支并更新
git checkout develop
git pull origin develop

# === 2. 创建功能分支 ===
# 使用规范命名创建新分支
git checkout -b feature/port-conflict-fix

# === 3. 开发代码 ===
# 编写代码...
# 修改文件: minimal-example/docker/ai-platform-nginx.conf

# === 4. 暂存修改 ===
# 查看修改状态
git status

# 添加特定文件到暂存区
git add minimal-example/docker/ai-platform-nginx.conf
git add docs/PORT_CONFLICT_RESOLUTION.md

# 或添加所有修改
git add .

# === 5. 提交代码 ===
# 使用规范格式提交
git commit -m "feat(docker): 添加AI平台统一入口配置

- 配置nginx反向代理到端口80
- 解决Dify平台端口冲突问题
- 更新访问地址为统一入口

Closes #123"

# === 6. 推送分支 ===
# 首次推送设置上游分支
git push -u origin feature/port-conflict-fix

# 后续推送
git push

# === 7. 创建合并请求 ===
# 在Git平台(GitHub/GitLab)创建Pull Request/Merge Request

# === 8. 合并后清理 ===
# 切换回主分支
git checkout develop
git pull origin develop

# 删除本地功能分支
git branch -d feature/port-conflict-fix
```

---

## 📝 命名规范

### 分支命名规范

| 分支类型 | 格式 | 示例 | 用途 |
|----------|------|------|------|
| **功能分支** | `feature/<功能描述>` | `feature/dify-integration` | 新功能开发 |
| **修复分支** | `bugfix/<问题描述>` | `bugfix/env-config-error` | Bug修复 |
| **热修复** | `hotfix/<紧急修复>` | `hotfix/security-patch` | 生产环境紧急修复 |
| **发布分支** | `release/<版本号>` | `release/v2025.6` | 版本发布准备 |

### Commit提交规范

采用 **Conventional Commits** 格式：
```
<类型>(作用域): <简短描述>

[详细描述]

[脚注]
```

#### 提交类型表

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加用户认证模块` |
| `fix` | Bug修复 | `fix: 修复端口冲突问题` |
| `docs` | 文档更新 | `docs: 更新部署指南` |
| `style` | 代码格式 | `style: 格式化Python代码` |
| `refactor` | 重构 | `refactor: 重构配置管理` |
| `test` | 测试 | `test: 添加API测试用例` |
| `chore` | 工具/构建 | `chore: 更新依赖版本` |

#### 提交示例

```bash
# ✅ 好的提交示例
git commit -m "feat(auth): 实现JWT用户认证

- 添加token生成和验证逻辑
- 集成Redis会话管理
- 支持权限级别控制

Closes #456"

git commit -m "fix(docker): 修复容器网络连接问题"

git commit -m "docs: 更新Git操作指南"

# ❌ 避免的提交示例
git commit -m "fix"
git commit -m "更新代码"
git commit -m "WIP"
```

---

## ⚔️ 冲突解决

### 合并冲突处理流程

```bash
# === 1. 拉取时发生冲突 ===
git pull origin develop
# Auto-merging README.md
# CONFLICT (content): Merge conflict in README.md

# === 2. 查看冲突文件 ===
git status
# You have unmerged paths.
# Unmerged paths:
#   both modified:   README.md

# === 3. 手动解决冲突 ===
# 编辑冲突文件，找到冲突标记：
```

**冲突文件示例**：
```markdown
# ZTZT AI中台解决方案

<<<<<<< HEAD
## 版本信息
当前版本: v2025.6
更新日期: 2025-06-26
=======
## 项目概述  
最新版本: v2025.7
发布时间: 2025-06-25
>>>>>>> develop
```

**手动解决后**：
```markdown
# ZTZT AI中台解决方案

## 版本信息
当前版本: v2025.6
更新日期: 2025-06-26
发布时间: 2025-06-25
```

```bash
# === 4. 标记冲突已解决 ===
git add README.md

# === 5. 完成合并 ===
git commit -m "merge: 合并develop分支并解决冲突"
```

### 变基冲突处理

```bash
# === 1. 变基时发生冲突 ===
git rebase develop
# CONFLICT (content): Merge conflict in config.py

# === 2. 解决冲突后继续 ===
# 编辑冲突文件...
git add config.py
git rebase --continue

# === 3. 如果想放弃变基 ===
git rebase --abort
```

### 冲突预防策略

```bash
# 每日同步最佳实践
git checkout develop
git pull origin develop
git checkout feature/your-branch
git rebase develop  # 保持历史清洁

# 推送前检查
git fetch origin
git rebase origin/develop
```

---

## 📋 快速参考

### 常用命令速查表

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看状态 | `git status` | 查看工作区状态 |
| 暂存文件 | `git add <file>` | 添加文件到暂存区 |
| 暂存所有 | `git add .` | 添加所有修改 |
| 提交代码 | `git commit -m "message"` | 提交到本地仓库 |
| 推送分支 | `git push origin <branch>` | 推送到远程仓库 |
| 拉取更新 | `git pull origin <branch>` | 拉取远程更新 |
| 创建分支 | `git checkout -b <branch>` | 创建并切换分支 |
| 切换分支 | `git checkout <branch>` | 切换到指定分支 |
| 删除分支 | `git branch -d <branch>` | 删除本地分支 |
| 查看历史 | `git log --oneline` | 查看提交历史 |

### ZTZT项目标准流程模板

#### 新功能开发模板
```bash
# 1. 准备环境
git checkout develop && git pull origin develop

# 2. 创建功能分支  
git checkout -b feature/<功能名称>

# 3. 开发提交
git add .
git commit -m "feat(<模块>): <功能描述>"

# 4. 推送分支
git push -u origin feature/<功能名称>

# 5. 创建PR/MR (在Git平台操作)

# 6. 合并后清理
git checkout develop && git pull origin develop
git branch -d feature/<功能名称>
```

#### 紧急修复模板
```bash
# 1. 基于main创建热修复分支
git checkout main && git pull origin main
git checkout -b hotfix/<修复描述>

# 2. 修复提交
git add .
git commit -m "hotfix: <修复描述>"

# 3. 推送并合并到main和develop
git push -u origin hotfix/<修复描述>
```

### 撤销操作速查

| 撤销场景 | 命令 | 说明 |
|----------|------|------|
| 撤销工作区修改 | `git checkout -- <file>` | 恢复文件到最后提交状态 |
| 撤销暂存 | `git reset HEAD <file>` | 取消文件暂存 |
| 撤销最后提交 | `git reset --soft HEAD~1` | 撤销提交保留修改 |
| 撤销并删除修改 | `git reset --hard HEAD~1` | 撤销提交删除修改 |
| 反向提交 | `git revert HEAD` | 创建反向提交 |

---

## 🎯 核心要点

### ✅ 良好实践
- **频繁小提交**: 每个功能点独立提交
- **清晰命名**: 分支和提交信息要表意明确  
- **及时同步**: 每日开始前同步主分支
- **代码审查**: 通过PR/MR进行团队审查

### ❌ 避免事项
- 大而全的提交包含多个不相关修改
- 模糊的分支名如 `temp`, `fix`, `test`
- 提交信息过于简单如 `update`, `fix`
- 直接向主分支推送代码

### 🚨 紧急情况处理
```bash
# 发现提交错误内容
git reset --soft HEAD~1  # 撤销但保留修改
# 重新整理后提交

# 推送后发现问题  
git revert HEAD  # 创建反向提交
git push origin <branch>

# 分支名字错误
git branch -m old-name new-name  # 重命名分支
```

---

**💡 记住**: 
- 提交前先 `git status` 检查状态
- 推送前先 `git pull` 同步更新  
- 有问题时使用 `git log` 查看历史
- 不确定时使用 `git stash` 暂存工作

**📞 获取帮助**: `git --help <command>` 查看命令帮助

---

*最后更新: 2025年6月26日*  
*版本: v2.0 (简化版)*  
*适用项目: ZTZT AI中台解决方案*
