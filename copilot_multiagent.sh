#!/usr/bin/env bash
# =============================================================================
# copilot_multiagent.sh  —— PRD → 功能的 Copilot 工作流启动脚本
#
# 版本: 2.1 (多账号/多模型 + 额度超额智能处理)
# 仓库: https://github.com/Huangwenyan28/font-project-test
#
# 用法:
#   ./copilot_multiagent.sh <功能名> [PRD路径] [--auto]    # 启动工作流
#   ./copilot_multiagent.sh config show                     # 查看配置
#   ./copilot_multiagent.sh config set model <模型名>         # 切换模型
#   ./copilot_multiagent.sh config set provider              # 配置自定义提供商
#   ./copilot_multiagent.sh profile list                     # 列出账号
#   ./copilot_multiagent.sh profile add <名称>               # 添加账号
#   ./copilot_multiagent.sh profile use <名称>               # 切换账号
#   ./copilot_multiagent.sh profile remove <名称>            # 删除账号
#
# 环境变量:
#   ALLOW_DIRTY=1   允许工作区存在 PRD 以外的未提交改动
#   COPILOT_MODEL   指定模型 (如 gpt-5.4, claude-sonnet-4)
# =============================================================================
set -euo pipefail

# ---------- 路径常量 ----------
CONFIG_DIR="${HOME}/.copilot-multiagent"
CONFIG_FILE="${CONFIG_DIR}/config.json"
PROFILES_DIR="${CONFIG_DIR}/profiles"
COPILOT_CONFIG_DIR="${HOME}/.config/github-copilot"
KEYCHAIN_SERVICE="copilot-multiagent"

# ---------- 颜色输出 ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}==>${NC} $*"; }
warn()  { echo -e "${YELLOW}==>${NC} $*"; }
error() { echo -e "${RED}==>${NC} $*" >&2; }
header(){ echo -e "${CYAN}$*${NC}"; }

# ---------- 初始化 ----------
init_config() {
  mkdir -p "${CONFIG_DIR}" "${PROFILES_DIR}"
  chmod 700 "${CONFIG_DIR}" "${PROFILES_DIR}"
  if [ ! -f "${CONFIG_FILE}" ]; then
    cat > "${CONFIG_FILE}" <<'JSON'
{
  "version": 2,
  "currentProfile": null,
  "defaultModel": null,
  "models": {
    "gpt-5.4":        { "name": "GPT-5.4", "type": "copilot" },
    "gpt-5.2":        { "name": "GPT-5.2", "type": "copilot" },
    "claude-sonnet-4":{ "name": "Claude Sonnet 4", "type": "copilot" },
    "o4-mini":        { "name": "O4 Mini", "type": "copilot" },
    "gemini-2.5-pro": { "name": "Gemini 2.5 Pro", "type": "copilot" }
  }
}
JSON
    chmod 600 "${CONFIG_FILE}"
  fi
}

# ---------- JSON 工具 ----------
read_json() {
  local key="$1" file="${2:-${CONFIG_FILE}}"
  python3 -c "import json,sys; d=json.load(open('${file}')); v=d.get('${key}'); print(v if isinstance(v,(str,int,float,bool,type(None))) else json.dumps(v))" 2>/dev/null || echo "null"
}
write_json() {
  local key="$1" value="$2" file="${3:-${CONFIG_FILE}}"
  python3 -c "
import json
d = json.load(open('${file}'))
d['${key}'] = json.loads('${value}') if '${value}' in ('true','false','null') or '${value}'.startswith('[') or '${value}'.startswith('{') else '${value}'
json.dump(d, open('${file}','w'), indent=2)
" 2>/dev/null && chmod 600 "${file}"
}
read_nested_json() {
  local keys="$1" file="${2:-${CONFIG_FILE}}"
  python3 -c "
import json
d = json.load(open('${file}'))
keys = '${keys}'.split('.')
for k in keys:
    d = d.get(k, {})
print(d if isinstance(d,(str,int,float,bool,type(None))) else json.dumps(d))
" 2>/dev/null || echo ""
}

# ---------- Keychain 工具 ----------
keychain_set() {
  local account="$1" value="$2"
  security delete-generic-password -s "${KEYCHAIN_SERVICE}" -a "${account}" 2>/dev/null || true
  security add-generic-password -s "${KEYCHAIN_SERVICE}" -a "${account}" -w "${value}" -U 2>/dev/null
}
keychain_get() {
  local account="$1"
  security find-generic-password -s "${KEYCHAIN_SERVICE}" -a "${account}" -w 2>/dev/null || echo ""
}
keychain_delete() {
  local account="$1"
  security delete-generic-password -s "${KEYCHAIN_SERVICE}" -a "${account}" 2>/dev/null || true
}

# ---------- 模型列表 ----------
list_models() {
  header "\n可用模型："
  echo "  Copilot 内置模型："
  python3 -c "
import json
d = json.load(open('${CONFIG_FILE}'))
for k, v in d.get('models', {}).items():
    print(f'    {k:25s}  {v.get(\"name\",k)}')
" 2>/dev/null
  echo ""
  echo "  BYOK（自定义提供商）:"
  echo "    使用 ./copilot_multiagent.sh config set provider 配置"
  echo ""
  echo "  当前模型: $(read_json defaultModel || echo '未设置')"
}

# =============================================================================
# 额度超额处理（核心新增功能）
# =============================================================================
handle_quota() {
  local exit_code="$1"
  shift

  # 如果命令成功，直接返回
  [ "$exit_code" = "0" ] && return 0

  # 检查输出中是否包含额度超限信息
  local output
  output="$("$@" 2>&1)" || true
  echo "$output"

  if echo "$output" | grep -qiE "(exceeded.*(quota|limit)|rate limit|quota exhausted|insufficient_quota)"; then
    echo ""
    header "═══════════════════════════════════════════════"
    warn "  Copilot 额度已用尽！"
    header "═══════════════════════════════════════════════"
    echo ""
    echo "  请选择："
    echo ""
    echo "  [1] 充值后重试"
    echo "      → 进入 https://github.com/settings/billing 充值"
    echo "      → 回到终端敲 copilot 继续刚才的工作"
    echo ""
    echo "  [2] 切换到另一个已保存的账号"
    echo "      → 如果你有其他有 Copilot 额度的 GitHub 号"
    echo ""
    echo "  [3] 用自己的 API Key"
    echo "      → 配置 BYOK 自定义提供商，不走 Copilot 额度"
    echo ""
    echo "  [q] 退出"
    echo ""

    while true; do
      read -r -p "请输入 [1/2/3/q]: " choice
      case "$choice" in
        1)
          info "已保存进度，充值后回来继续："
          echo "  copilot --continue   # 继续上次的会话"
          echo ""
          echo "充值链接: https://github.com/settings/billing"
          return 1
          ;;
        2)
          switch_profile_interactive
          # 切换成功后重试
          env_cmd=$(build_env)
          echo ""
          info "已切换到新账号，正在重试..."
          echo ""
          eval "${env_cmd} $*"
          return $?
          ;;
        3)
          echo ""
          configure_provider_interactive
          # 配置成功后重试
          env_cmd=$(build_env)
          echo ""
          info "已配置 API Key，正在重试..."
          echo ""
          eval "${env_cmd} $*"
          return $?
          ;;
        q|Q)
          info "已退出"
          return 1
          ;;
        *)
          echo "  无效选项，请重新选择"
          ;;
      esac
    done
  fi

  # 不是额度问题，原样返回
  return "$exit_code"
}

# ---------- 交互式账号切换 ----------
switch_profile_interactive() {
  local profiles=()
  for pdir in "${PROFILES_DIR}"/*/; do
    if [ -d "$pdir" ]; then
      profiles+=("$(basename "$pdir")")
    fi
  done

  if [ ${#profiles[@]} -eq 0 ]; then
    warn "没有已保存的账号"
    echo ""
    echo "请先添加一个账号："
    echo "  ./copilot_multiagent.sh profile add <账号名称>"
    echo ""
    read -r -p "输入新账号名称: " new_name
    if [ -n "$new_name" ]; then
      cmd_profile_add "$new_name"
    fi
    return
  fi

  echo "  已保存的账号:"
  for i in "${!profiles[@]}"; do
    local marker=""
    local current=$(read_json currentProfile)
    [ "${profiles[$i]}" = "$current" ] && marker=" ← 当前"
    echo "    [$((i+1))] ${profiles[$i]}${marker}"
  done
  echo ""
  read -r -p "选择账号编号 (1-${#profiles[@]}): " idx
  if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "${#profiles[@]}" ]; then
    cmd_profile_use "${profiles[$((idx-1))]}"
  else
    error "无效选择"
  fi
}

# ---------- 交互式提供商配置 ----------
configure_provider_interactive() {
  header "\n配置自定义模型提供商 (BYOK)"
  echo "  支持 OpenAI、DeepSeek、Anthropic、Ollama 等"
  echo ""
  read -r -p "提供商类型 (openai/azure/anthropic, 默认 openai): " ptype
  ptype="${ptype:-openai}"
  read -r -p "API 端点 URL (如 https://api.deepseek.com/v1): " base_url
  read -r -s -p "API Key (将安全存入 macOS Keychain): " api_key
  echo ""
  read -r -p "模型名称 (如 deepseek-chat, gpt-4): " model_name

  python3 -c "
import json
d = json.load(open('${CONFIG_FILE}'))
d['provider'] = {'type': '${ptype}', 'baseUrl': '${base_url}'}
json.dump(d, open('${CONFIG_FILE}','w'), indent=2)
" 2>/dev/null
  chmod 600 "${CONFIG_FILE}"

  if [ -n "$api_key" ]; then
    keychain_set "provider-api-key" "$api_key"
    info "API Key 已安全存入 macOS Keychain"
  fi
  if [ -n "$model_name" ]; then
    write_json defaultModel "$model_name"
    info "默认模型已设为: ${model_name}"
  fi
}

# =============================================================================
# 配置命令
# =============================================================================
cmd_config() {
  local sub="${2:-show}"
  case "$sub" in
    show)
      header "\n======================= 当前配置 ======================="
      echo "  配置文件: ${CONFIG_DIR}"
      echo ""
      local profile=$(read_json currentProfile)
      local model=$(read_json defaultModel)
      [ "$profile" = "null" ] && profile="未设置"
      [ "$model" = "null" ] && model="未设置"
      echo "  当前账号: ${profile}"
      echo "  默认模型: ${model}"

      local provider_type
      provider_type=$(read_nested_json "provider.type")
      if [ -n "$provider_type" ] && [ "$provider_type" != "{}" ]; then
        local base_url
        base_url=$(read_nested_json "provider.baseUrl")
        echo "  提供商: ${provider_type}"
        echo "  端点: ${base_url}"
        local key_status
        key_status=$(keychain_get "provider-api-key" && echo "已存入 Keychain 🔒" || echo "未设置")
        echo "  API Key: ${key_status}"
      fi

      echo ""
      echo "  已保存账号:"
      local has_profiles=0
      for pdir in "${PROFILES_DIR}"/*/; do
        if [ -d "$pdir" ]; then
          local pname=$(basename "$pdir")
          local marker=""
          [ "$pname" = "$(read_json currentProfile)" ] && marker=" ← 当前"
          local pmodel=$(read_nested_json "model" "${pdir}profile.json" 2>/dev/null)
          [ -z "$pmodel" ] && pmodel="默认"
          echo "    - ${pname}${marker}  (模型: ${pmodel})"
          has_profiles=1
        fi
      done
      [ "$has_profiles" = "0" ] && echo "    (无)"
      echo "========================================================="
      ;;
    set)
      local what="${3:-}"
      case "$what" in
        model)
          local model_name="${4:-}"
          if [ -z "$model_name" ]; then
            list_models
            echo ""
            read -r -p "输入模型名称: " model_name
          fi
          [ -z "$model_name" ] && { error "模型名称不能为空"; exit 1; }
          write_json defaultModel "$model_name"
          info "默认模型已设为: ${model_name}"
          echo "  提示: 也可通过环境变量 COPILOT_MODEL=${model_name} 临时覆盖"
          ;;
        provider)
          configure_provider_interactive
          ;;
        *)
          error "用法: ./copilot_multiagent.sh config set model|provider [值]"
          exit 1
          ;;
      esac
      ;;
    *)
      error "用法: ./copilot_multiagent.sh config show|set"
      exit 1
      ;;
  esac
}

# =============================================================================
# 账号管理
# =============================================================================
cmd_profile_add() {
  local pname="$1"
  local pdir="${PROFILES_DIR}/${pname}"
  if [ -d "$pdir" ]; then
    warn "账号 '${pname}' 已存在，将覆盖"
  fi

  header "\n正在为 '${pname}' 配置 Copilot 账号"
  echo "  即将启动 copilot login，请在浏览器完成 GitHub 认证"
  echo "  登录的 GitHub 账号需要有 Copilot 订阅"
  echo ""
  read -r -p "按回车继续 (Ctrl+C 取消)..."

  mkdir -p "$pdir"
  if [ -d "${COPILOT_CONFIG_DIR}" ]; then
    cp -r "${COPILOT_CONFIG_DIR}/." "${pdir}/copilot-config/" 2>/dev/null || true
  fi

  info "启动 copilot login..."
  copilot login 2>&1 || true

  mkdir -p "${pdir}/copilot-config"
  if [ -d "${COPILOT_CONFIG_DIR}" ]; then
    cp -r "${COPILOT_CONFIG_DIR}/." "${pdir}/copilot-config/" 2>/dev/null || true
  fi

  local model=$(read_json defaultModel)
  [ "$model" = "null" ] && model=""
  cat > "${pdir}/profile.json" <<JSON
{
  "name": "${pname}",
  "model": ${model:+""${model}""}${model:-null},
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
  chmod 600 "${pdir}/profile.json"
  write_json currentProfile "$pname"
  info "账号 '${pname}' 添加成功并设为当前账号"
}

cmd_profile_use() {
  local pname="$1"
  local pdir="${PROFILES_DIR}/${pname}"
  if [ ! -d "$pdir" ]; then
    error "账号 '${pname}' 不存在"
    return 1
  fi
  if [ ! -d "${pdir}/copilot-config" ]; then
    error "账号 '${pname}' 的认证信息不完整"
    echo "  请重新运行: ./copilot_multiagent.sh profile add ${pname}"
    return 1
  fi

  local backup_dir="${CONFIG_DIR}/_last_config"
  if [ -d "${COPILOT_CONFIG_DIR}" ]; then
    mkdir -p "$backup_dir"
    cp -r "${COPILOT_CONFIG_DIR}/." "${backup_dir}/" 2>/dev/null || true
  fi

  rm -rf "${COPILOT_CONFIG_DIR}" 2>/dev/null || true
  mkdir -p "${COPILOT_CONFIG_DIR}"
  cp -r "${pdir}/copilot-config/." "${COPILOT_CONFIG_DIR}/" 2>/dev/null || true

  write_json currentProfile "$pname"
  local pmodel
  pmodel=$(read_nested_json "model" "${pdir}/profile.json" 2>/dev/null)
  if [ -n "$pmodel" ] && [ "$pmodel" != "null" ]; then
    write_json defaultModel "$pmodel"
  fi
  info "已切换到账号: ${pname}"
}

cmd_profile() {
  local sub="${2:-list}"
  case "$sub" in
    list)
      header "\n已保存的账号:"
      local current=$(read_json currentProfile)
      local count=0
      for pdir in "${PROFILES_DIR}"/*/; do
        if [ -d "$pdir" ]; then
          local pname=$(basename "$pdir")
          local marker=""
          [ "$pname" = "$current" ] && marker=" ← 当前"
          local pmodel=$(read_nested_json "model" "${pdir}profile.json" 2>/dev/null)
          [ -z "$pmodel" ] || [ "$pmodel" = "null" ] && pmodel="未设置"
          echo "  - ${pname}${marker}  (模型: ${pmodel})"
          count=$((count + 1))
        fi
      done
      [ "$count" = "0" ] && echo "  (暂无保存的账号)"
      echo ""
      echo "添加:  ./copilot_multiagent.sh profile add <名称>"
      echo "切换:  ./copilot_multiagent.sh profile use <名称>"
      echo "删除:  ./copilot_multiagent.sh profile remove <名称>"
      ;;
    add)
      local pname="${3:-}"
      if [ -z "$pname" ]; then
        read -r -p "新账号名称 (如 work/personal): " pname
      fi
      [ -z "$pname" ] && { error "账号名称不能为空"; exit 1; }
      cmd_profile_add "$pname"
      ;;
    use)
      local pname="${3:-}"
      if [ -z "$pname" ]; then
        error "用法: ./copilot_multiagent.sh profile use <名称>"
        cmd_profile list 2>&1 | grep -v "^$" | head -20
        exit 1
      fi
      cmd_profile_use "$pname"
      ;;
    remove)
      local pname="${3:-}"
      if [ -z "$pname" ]; then
        error "用法: ./copilot_multiagent.sh profile remove <名称>"
        exit 1
      fi
      local pdir="${PROFILES_DIR}/${pname}"
      [ ! -d "$pdir" ] && { error "账号 '${pname}' 不存在"; exit 1; }
      warn "即将删除账号 '${pname}'！"
      read -r -p "确认删除? (y/N): " confirm
      if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        info "已取消"; exit 0
      fi
      rm -rf "$pdir"
      local current=$(read_json currentProfile)
      [ "$current" = "$pname" ] && write_json currentProfile null
      info "账号 '${pname}' 已删除"
      ;;
    *)
      error "用法: ./copilot_multiagent.sh profile list|add|use|remove"
      exit 1
      ;;
  esac
}

# =============================================================================
# 构建环境变量
# =============================================================================
build_env() {
  local env_cmd=""
  local model="${COPILOT_MODEL:-}"
  if [ -z "$model" ]; then
    model=$(read_json defaultModel)
    [ "$model" = "null" ] && model=""
  fi
  if [ -z "$model" ]; then
    local profile=$(read_json currentProfile)
    if [ "$profile" != "null" ] && [ -n "$profile" ]; then
      model=$(read_nested_json "model" "${PROFILES_DIR}/${profile}/profile.json" 2>/dev/null)
      [ "$model" = "null" ] && model=""
    fi
  fi
  if [ -n "$model" ]; then
    env_cmd="export COPILOT_MODEL=${model}; "
  fi

  local provider_type
  provider_type=$(read_nested_json "provider.type")
  if [ -n "$provider_type" ] && [ "$provider_type" != "{}" ]; then
    local base_url
    base_url=$(read_nested_json "provider.baseUrl")
    local api_key
    api_key=$(keychain_get "provider-api-key") || true
    [ -n "$base_url" ] && env_cmd+="export COPILOT_PROVIDER_BASE_URL=${base_url}; "
    [ -n "$provider_type" ] && env_cmd+="export COPILOT_PROVIDER_TYPE=${provider_type}; "
    [ -n "$api_key" ] && env_cmd+="export COPILOT_PROVIDER_API_KEY=${api_key}; "
  fi
  echo "$env_cmd"
}

# =============================================================================
# 主工作流
# =============================================================================
main() {
  init_config
  local cmd="${1:-}"
  case "$cmd" in
    config|profile)
      "cmd_${cmd}" "$@"
      exit 0
      ;;
    run)
      init_config
      env_cmd=$(build_env)
      model_flag=""
      local cm=$(read_json defaultModel)
      [ "$cm" != "null" ] && [ -n "$cm" ] && model_flag="--model $cm"
      shift
      local prompt="$*"
      if [ -z "$prompt" ]; then
        echo "启动 Copilot（带模型/账号配置 + 额度监控）..."
        handle_quota 0 eval "${env_cmd} copilot ${model_flag}" || true
      else
        handle_quota 0 eval "${env_cmd} copilot -p "$prompt" ${model_flag}" || true
      fi
      ;;
    help|--help|-h)
      header "\n用法:"
      echo "  ./copilot_multiagent.sh <功能名> [PRD路径] [--auto]"
      echo "  ./copilot_multiagent.sh config show|set      管理配置"
      echo "  ./copilot_multiagent.sh profile list|add|use  管理账号"
      echo "  ./copilot_multiagent.sh run [prompt]          启动 copilot（带额度监控）"
      echo ""
      echo "示例:"
      echo "  ./copilot_multiagent.sh user-notifications          # 工作流"
      echo "  ./copilot_multiagent.sh config set model gpt-5.4    # 切模型"
      echo "  ./copilot_multiagent.sh profile add work            # 加账号"
      echo "  ./copilot_multiagent.sh profile use work            # 切账号"
      echo "  ./copilot_multiagent.sh run                        # 启动 copilot（推荐）"
      exit 0      ;;
  esac

  local FEATURE="${1:?用法: ./copilot_multiagent.sh <功能名> [PRD路径] [--auto]}"
  local PRD="docs/PRD.md"
  local AUTO=0
  for a in "${@:2}"; do
    case "$a" in
      --auto) AUTO=1 ;;
      *)      PRD="$a" ;;
    esac
  done
  local BRANCH="feature/$FEATURE"

  echo "==> 1/6 检查 Copilot CLI + Superpowers"
  command -v copilot >/dev/null 2>&1 || { error "未装 copilot: npm install -g @github/copilot"; exit 1; }
  copilot plugin marketplace add obra/superpowers-marketplace 2>/dev/null || true
  copilot plugin install superpowers@superpowers-marketplace 2>/dev/null || true

  local env_cmd
  env_cmd=$(build_env)
  local current_model="${COPILOT_MODEL:-$(read_json defaultModel)}"
  [ "$current_model" = "null" ] && current_model=""
  local current_profile=$(read_json currentProfile)
  [ "$current_profile" = "null" ] && current_profile=""

  if [ -n "$current_model" ]; then info "当前模型: ${current_model}"; fi
  if [ -n "$current_profile" ]; then info "当前账号: ${current_profile}"; fi

  echo "==> 2/6 确认在 git 仓库内"
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { error "当前目录不是 git 仓库。"; exit 1; }

  echo "==> 3/6 检查工作区是否干净（PRD 文件除外）"
  local DIRTY
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
  if ! git diff --quiet -- "$PRD" || [ -n "$(git ls-files --others --exclude-standard -- "$PRD")" ]; then
    git add "$PRD"
    git commit -qm "docs: PRD for $FEATURE"
  fi

  echo "==> 6/6 备好四段 prompt 到 .fleet/prompts.md"
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
  [ -n "$current_model" ] && echo " 模型: $current_model"
  [ -n "$current_profile" ] && echo " 账号: $current_profile"
  echo " Prompt 备份: .fleet/prompts.md"
  echo "============================================================"

  if [ "$AUTO" = "1" ]; then
    echo "==> 无人值守模式"
    local model_flag=""
    [ -n "$current_model" ] && model_flag="--model ${current_model}"
    local cmdline="copilot -p \"Use superpowers. 按 ${PRD} 实现功能：先 explore 现有代码做设计，再 writing-plans 拆成并行 track（共享文件归串行前置 track），然后 /fleet 执行，每个 track 走 TDD，最后跑全量测试确认无回归。\" --no-ask-user ${model_flag}"
    # 额度检测 + 自动处理
    handle_quota 0 eval "${env_cmd} ${cmdline}" || true
  else
    echo "下一步（交互模式）："
    echo "  copilot                       # 起会话"
    echo "  /skills                       # 确认 superpowers 在"
    echo "  然后从 .fleet/prompts.md 依次粘 PROMPT-1..4"
    echo ""
    echo "快速启动（直接带模型和账号配置）："
    echo "  eval \"\$(./copilot_multiagent.sh _env)\" && copilot"
    echo ""
    echo "额度超额时系统会提示切换账号或配置 API Key"
    echo ""
    echo "跑砸了随时丢弃：  git switch main && git branch -D $BRANCH"
  fi
}

# 生成环境变量
if [ "${1:-}" = "_env" ]; then
  init_config
  build_env
  exit 0
fi

main "$@"
