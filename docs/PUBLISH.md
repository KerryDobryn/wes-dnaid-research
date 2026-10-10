# 上传 GitHub

本包只包含清理过的源码、合成例子和文档。真实分析目录、私密密钥和当前个人 ID 均没有导入。请从本仓库目录开始创建版本库，勿对外层项目目录初始化并整体上传。

```sh
git init
git add README.md LICENSE pyproject.toml .gitignore dnaid tests examples docs workflows .github
git diff --cached --stat
git diff --cached
python3 -m unittest discover -s tests -v
git commit -m "Initial research DNA ID prototype with synthetic examples"
git branch -M main
```

在 GitHub 上新建空仓库（不预置 README），然后按照 GitHub 显示的远程地址执行 `git remote add origin ...` 和 `git push -u origin main`。源码可以公开；真实应用材料请留在仓库外。本地包尚未创建远程仓库或推送。

许可证默认为 MIT，仅适用于这里的代码与文档；若希望变更许可证，请在首次发布前完成。每次发布应记录编码协议、质控实现和依赖版本；测试通过后再打标签。0.1.0 是研究预览，不能视为临床或认证产品。
