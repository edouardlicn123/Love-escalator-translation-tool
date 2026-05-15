# Git 初始化配置

首次安装 Git 后需要配置用户名和邮箱，否则无法提交。

## 基本配置

```bash
# 设置用户名
git config --global user.name "Your Name"

# 设置邮箱
git config --global user.email "your.email@example.com"

# 设置默认分支名为 main
git config --global init.defaultBranch main

# 设置换行符处理（Linux/macOS 用 input，Windows 用 true）
git config --global core.autocrlf input
```

## 查看配置

```bash
git config --list --global
```

## 初始化本地仓库并连接 GitHub

```bash
# 1. 初始化本地仓库
git init

# 2. 添加所有文件到暂存区
git add .

# 3. 创建第一个提交
git commit -m "Initial commit"

# 4. 添加远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 5. 推送到 GitHub
git push -u origin main
```

> 如果默认分支是 `master`，将第 5 步的 `main` 改为 `master`。
> 如果远程已有内容，推送前先执行 `git pull origin main --rebase`。

## 生成 SSH Key

用于免密码连接 GitHub。

```bash
# 生成密钥（替换邮箱）
ssh-keygen -t ed25519 -C "your.email@example.com"
# 一路回车使用默认路径

# 查看公钥（复制输出内容）
cat ~/.ssh/id_ed25519.pub
```

把公钥添加到 GitHub → Settings → SSH and GPG keys → New SSH key。
