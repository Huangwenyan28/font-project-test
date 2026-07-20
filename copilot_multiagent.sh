#!/usr/bin/env bash
# prd-to-feature.sh —— 在【已有真实仓库】上跑 PRD → 功能 的流。
# 与 demo 脚本的根本区别：不造任何脚手架、绝不 rm，只做安全准备。
#
# 用法:
#   ./prd-to-feature.sh <功能名> [PRD路径(默认 docs/PRD.md)] [--auto]
#   ALLOW_DIRTY=1 ./prd-to-feature.sh ...   # 允许工作区有其他未提交改动
#
# 在你的仓库根目录运行。
set -euo pipefail

FEATURE="${1:?用法: ./prd-to-feature.sh <功能名> [PRD路径] [--auto]}"
PRD="docs/PRD.md"
AUTO=0
for a in "${@:2}"; do
  case "$a" in
    --auto) AUTO=1 ;;
    *)      PRD="$a" ;;
  esac
done
BRANCH="feature/$FEATURE"

echo "==> 1/6 检查 Copilot CLI + Superpowers"
command -v copilot >/dev/null 2>&1 || { echo "未装 copilot: npm install -g @github/copilot"; exit 1; }
copilot plugin marketplace add obra/superpowers-marketplace 2>/dev/null || true
copilot plugin install superpowers@superpowers-marketplace 2>/dev/null || true

echo "==> 2/6 确认在 git 仓库内"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "当前目录不是 git 仓库。"; exit 1; }

echo "==> 3/6 检查工作区是否干净（PRD 文件除外）"
# 注意: git 会把"整个未跟踪目录"折叠成一行(如 ?? docs/)，导致按完整路径排除失效。
# -uall 强制逐个列出未跟踪文件; pathspec :(exclude) 精确排除 PRD 本身。
DIRTY="$(git status --porcelain -uall -- . ":(exclude)$PRD")"
if [ -n "$DIRTY" ] && [ "${ALLOW_DIRTY:-0}" != "1" ]; then
  echo "工作区有未提交改动，先 commit/stash，或用 ALLOW_DIRTY=1 覆盖："
  echo "$DIRTY"
  exit 1
fi

echo "==> 4/6 处理 PRD: $PRD"
if [ ! -f "$PRD" ]; then
  mkdir -p "$(dirname "$PRD")"
  cat > "$PRD" <<'MD'
# PRD: <功能名>

## 背景 / 要解决的问题

## 目标（这次要达成什么）

## 功能点（尽量拆成可独立实现的点，每点对应清晰产物）
- [ ]
- [ ]

## 验收标准（怎么算完成，尽量可测）

## 明确不做的（范围外，防止 agent 越界）
MD
  echo "    已生成 PRD 模板：$PRD"
  echo "    >>> 填好内容后重新运行本脚本。"
  exit 0
fi

echo "==> 5/6 切到隔离分支: $BRANCH"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git switch "$BRANCH"
else
  git switch -c "$BRANCH"
fi
# 如果 PRD 有未提交改动则先提交，保证后续 /fleet 的 diff 干净
if ! git diff --quiet -- "$PRD" || [ -n "$(git ls-files --others --exclude-standard -- "$PRD")" ]; then
  git add "$PRD"
  git commit -qm "docs: PRD for $FEATURE"
fi

echo "==> 6/6 备好四段 prompt 到 .fleet/prompts.md（方便复制）"
mkdir -p .fleet
grep -qxF ".fleet/" .gitignore 2>/dev/null || echo ".fleet/" >> .gitignore
cat > .fleet/prompts.md <<MD
# 依次粘贴（每段之间等它完成、你确认后再下一段）

## PROMPT-1 探索+设计  → 确认落点文件后说"批准，写计划"
Use superpowers. PRD 在 ${PRD}。先不要写代码，也先不要 /fleet。
1. 读 ${PRD}。
2. 用 explore 子 agent 摸清现有代码里和这份 PRD 相关的部分：涉及哪些模块/文件、现有架构和约定、相关测试在哪、有无可复用项。
3. 按 brainstorming 反问 PRD 里不清楚的点。
4. 产出设计文档：每个功能点明确落到哪些现有文件(改)和新文件(增)，是否符合现有架构。分段给我确认。

## PROMPT-2 拆并行 track  → 确认共享文件归前置 track 后说"批准"
设计批准。用 writing-plans 拆成可并行的 track。每个 track 必须：对应一个可验证产物、列出改/增的文件、列出"不许碰的文件"、标注依赖。
关键：把多个 track 都要改的共享文件(路由/schema/类型/迁移/依赖清单)单独拎成一个【串行前置 track】，一个人改，其余 track 等它完再并行。先只给分解，不要执行。

## PROMPT-3 执行
分解批准。/fleet 先跑串行前置 track，完成后并行跑其余。约束：严格按文件边界，不碰他人文件；共享文件只由前置 track 改；不在 PRD 范围外重构；每 track 走 TDD；完成判据=新测试过且现有全量测试不回归。每个子 agent 完成后汇报改了什么、跑了什么、结果。

## PROMPT-4 review+验证
用 requesting-code-review 和 verification-before-completion 收尾：跑全量测试+lint+类型检查确认无回归；review 各 track 是否冲突、是否都在 PRD 范围内；给我总结。
MD

echo
echo "============================================================"
echo " 准备完成。分支: $BRANCH   PRD: $PRD"
echo " Prompt 备份: .fleet/prompts.md"
echo "============================================================"

if [ "$AUTO" = "1" ]; then
  echo "==> 无人值守模式：直接 /fleet 跑（建议建立信任后再用）"
  copilot -p "Use superpowers. 按 ${PRD} 实现功能：先 explore 现有代码做设计，再 writing-plans 拆成并行 track（共享文件归串行前置 track），然后 /fleet 执行，每个 track 走 TDD，最后跑全量测试确认无回归。" --no-ask-user
else
  echo "下一步（交互模式，推荐首次用）："
  echo "  copilot                       # 起会话，确认信任目录"
  echo "  /skills                       # 确认 superpowers 在"
  echo "  然后从 .fleet/prompts.md 依次粘 PROMPT-1..4"
  echo "  首次建议：PROMPT-2 后 Shift+Tab 进 plan mode 核对分解，再放 /fleet"
  echo
  echo "跑砸了随时丢弃：  git switch main && git branch -D $BRANCH"
fi
