<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import TabSwitcher from '@/components/ui/TabSwitcher.vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import SecretInput from '@/components/ui/SecretInput.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import MsIcon from '@/components/ui/MsIcon.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import HelpTip from '@/components/ui/HelpTip.vue'
import UnsavedBanner from '@/components/ui/UnsavedBanner.vue'
import FormField from '@/components/form/FormField.vue'
import BaseSelect from '@/components/form/BaseSelect.vue'
import FieldControlRow from '@/components/form/FieldControlRow.vue'
import { useApiFetch } from '@/composables/useApiFetch'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useUnsavedGuard } from '@/composables/useUnsavedGuard'
import { usePromptSettings } from '@/composables/generate/usePromptSettings'
import { useAppStore } from '@/stores/app'
import { apiErrorText, apiMessageText, type ApiErrorBody } from '@/utils/apiError'
import type {
  LlmProviderConfig,
  ModelOption,
  LlmConfigData,
} from '@/types/settings'

defineOptions({ name: 'SettingsPage' })

const { t, te } = useI18n({ useScope: 'global' })
const { get, post, put } = useApiFetch()
const { toast } = useToast()
const { confirm } = useConfirm()
const app = useAppStore()

// ─── Prompt editor settings ───────────────────────────────────────────────────

const {
  settings: promptSettings,
  saving: promptSaving,
  isDirty: promptFormDirty,
  translateProviders: promptTranslateProviders,
  load: loadPromptSettings,
  save: savePromptSettings,
  discard: discardPromptSettings,
} = usePromptSettings()

const promptAutocompleteOptions = [
  { value: 10, label: '10' },
  { value: 20, label: '20' },
  { value: 50, label: '50' },
]

const normalizeEnabled = computed(() =>
  promptSettings.normalize_comma
  || promptSettings.normalize_period
  || promptSettings.normalize_bracket
  || promptSettings.normalize_underscore
  || promptSettings.escape_bracket,
)

function toggleNormalizeAll(on: boolean) {
  if (on) {
    // 开启总开关 → 恢复默认值
    promptSettings.normalize_comma = true
    promptSettings.normalize_period = true
    promptSettings.normalize_bracket = true
  } else {
    // 关闭总开关 → 全部关闭
    promptSettings.normalize_comma = false
    promptSettings.normalize_period = false
    promptSettings.normalize_bracket = false
    promptSettings.normalize_underscore = false
    promptSettings.escape_bracket = false
  }
}

const translateProviderOptions = computed(() => [
  { value: '', label: t('settings.prompt.translation.provider_auto') },
  ...promptTranslateProviders.value.map(p => ({
    value: p,
    label: t(`settings.prompt.translation.providers.${p}`, p),
  })),
])

// ─── Tab state ────────────────────────────────────────────────────────────────

const repoUrl = 'https://github.com/vvb7456/ComfyCarry'
const dockerHubUrl = 'https://hub.docker.com/r/erocraft/comfycarry'
const erocraftUrl = 'https://www.erocraft.com/'
const copyrightRange = `2015–${new Date().getFullYear()}`

const activeTab = ref('comfycarry')
const tabs = computed(() => [
  { key: 'comfycarry', label: 'ComfyCarry', icon: 'dashboard' },
  { key: 'prompt', label: t('settings.prompt.tab_label'), icon: 'edit_note' },
  { key: 'civitai', label: 'CivitAI', icon: 'palette' },
  { key: 'llm', label: 'LLM', icon: 'smart_toy' },
])

// ─── Password state ───────────────────────────────────────────────────────────

const pwCurrent = ref('')
const pwNew = ref('')
const pwConfirm = ref('')
const pwSubmitting = ref(false)

// ─── API Key state ────────────────────────────────────────────────────────────

const apiKey = ref('')
const apiKeyRevealed = ref(false)
const regenLoading = ref(false)

// ─── CivitAI state ────────────────────────────────────────────────────────────

const civitaiKey = ref('')
const civitaiSaving = ref(false)

// ─── Reinit state ─────────────────────────────────────────────────────────────

const reinitKeepModels = ref(true)
const reinitLoading = ref(false)

// ─── Update state ─────────────────────────────────────────────────────────────

const updateChecking = ref(false)
const updateApplying = ref(false)
const updateInfo = ref<{
  current_version?: string
  current_commit?: string
  latest_version?: string
  latest_name?: string
  latest_message?: string
  has_update?: boolean
} | null>(null)
const updatePhase = ref('')
const updateActionLabel = computed(() => {
  if (updateChecking.value) return t('settings.update.checking')
  if (updateApplying.value) return t('settings.update.applying')
  return updateInfo.value?.has_update
    ? t('settings.update.apply_btn')
    : t('settings.update.check_btn')
})

function localizedUpdatePhase(phase: string, fallback = '') {
  const key = `settings.update.phase.${phase}`
  return te(key) ? t(key) : (fallback || phase)
}

async function runUpdateAction() {
  if (updateChecking.value || updateApplying.value) return
  if (updateInfo.value?.has_update) {
    await applyUpdate()
  } else {
    await checkUpdate()
  }
}

async function checkUpdate() {
  updateChecking.value = true
  updateInfo.value = null
  updatePhase.value = ''
  const data = await get<{
    current_version: string
    current_commit: string
    latest_version: string
    latest_name: string
    latest_message: string
    has_update: boolean
  }>('/api/update/check')
  updateChecking.value = false
  if (!data) return
  updateInfo.value = data
}

async function applyUpdate() {
  if (!await confirm({ message: t('settings.update.apply_btn') + '?' })) return
  updateApplying.value = true
  updatePhase.value = t('settings.update.applying')
  let terminalPhase = false
  let updateCompleted = false
  try {
    const resp = await fetch('/api/update/apply', { method: 'POST' })
    if (!resp.ok) {
      let message = t('settings.update.error')
      try { message = apiErrorText(await resp.json(), message) } catch { /* ignore parse errors */ }
      toast(message, 'error')
      return
    }
    if (!resp.body) {
      toast(t('settings.update.error'), 'error')
      return
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const ev = JSON.parse(line.slice(6))
          updatePhase.value = localizedUpdatePhase(ev.phase, ev.message)
          if (ev.phase === 'done') {
            terminalPhase = true
            updateCompleted = true
            toast(t('settings.update.done'), 'success')
            setTimeout(() => {
              updateApplying.value = false
              location.reload()
            }, 4000)
          } else if (ev.phase === 'error') {
            terminalPhase = true
            toast(`${t('settings.update.error')}: ${ev.message}`, 'error')
          }
        } catch { /* ignore parse errors */ }
      }
    }
    if (!terminalPhase) toast(t('settings.update.error'), 'error')
  } catch (e: any) {
    toast(`${t('settings.update.error')}: ${e.message}`, 'error')
  } finally {
    if (!updateCompleted) {
      updateApplying.value = false
      updatePhase.value = ''
    }
  }
}

// ─── LLM state ───────────────────────────────────────────────────────────────

const llmProvidersLoaded = ref(false)
const llmProvider = ref('')
const llmApiKey = ref('')
const llmBaseUrl = ref('')
const llmModel = ref('')
const llmTemperature = ref(0.7)
const llmMaxTokens = ref(2000)
const llmStream = ref(true)
const llmAllModels = ref<ModelOption[]>([])
const selectedLlmModel = ref<ModelOption | null>(null)
const llmModelInfo = computed(() => {
  const m = selectedLlmModel.value
  if (!m) return ''
  const parts: string[] = []
  if (m.context_length) parts.push(t('settings.llm.model.context_fmt', { n: m.context_length.toLocaleString() }))
  if (m.pricing?.prompt) parts.push(t('settings.llm.model.input_fmt', { n: m.pricing.prompt }))
  if (m.pricing?.completion) parts.push(t('settings.llm.model.output_fmt', { n: m.pricing.completion }))
  return parts.join(' · ')
})
const llmFetchingModels = ref(false)
const llmSaving = ref(false)
const llmTesting = ref(false)
const llmTestResult = ref<{ ok: boolean; message: string } | null>(null)
const llmProviderKeys = ref<Record<string, LlmProviderConfig>>({})

type LlmProviderOption = {
  id: string
  labelKey: string
  baseUrlKind: 'openai' | 'anthropic' | 'none'
}

/** Provider IDs encode the wire protocol so the UI cannot create an invalid
 * provider/protocol pair. */
const LLM_PROVIDER_OPTIONS: LlmProviderOption[] = [
  { id: 'openai', labelKey: 'settings.llm.provider.openai', baseUrlKind: 'none' },
  { id: 'deepseek', labelKey: 'settings.llm.provider.deepseek', baseUrlKind: 'none' },
  { id: 'openrouter', labelKey: 'settings.llm.provider.openrouter', baseUrlKind: 'none' },
  { id: 'anthropic', labelKey: 'settings.llm.provider.anthropic', baseUrlKind: 'none' },
  { id: 'gemini', labelKey: 'settings.llm.provider.gemini', baseUrlKind: 'none' },
  { id: 'custom_openai', labelKey: 'settings.llm.provider.custom_openai', baseUrlKind: 'openai' },
  { id: 'custom_responses', labelKey: 'settings.llm.provider.custom_responses', baseUrlKind: 'openai' },
  { id: 'custom_anthropic', labelKey: 'settings.llm.provider.custom_anthropic', baseUrlKind: 'anthropic' },
]

function providerOption(providerId: string): LlmProviderOption | undefined {
  return LLM_PROVIDER_OPTIONS.find(p => p.id === providerId)
}

const llmProviderOptions = computed(() =>
  LLM_PROVIDER_OPTIONS.map(option => ({
    value: option.id,
    label: t(option.labelKey),
  })),
)

const llmModelSelectOptions = computed(() =>
  llmAllModels.value.map(m => ({ value: m.id, label: m.name || m.id }))
)

const showLlmBaseUrl = computed(() => {
  const kind = providerOption(llmProvider.value)?.baseUrlKind
  return !!kind && kind !== 'none'
})
const llmBaseUrlHelp = computed(() =>
  providerOption(llmProvider.value)?.baseUrlKind === 'anthropic'
    ? t('settings.llm.provider.base_url_help_anthropic')
    : t('settings.llm.provider.base_url_help_openai'),
)
const llmBaseUrlPlaceholder = computed(() =>
  providerOption(llmProvider.value)?.baseUrlKind === 'anthropic'
    ? t('settings.llm.provider.base_url_placeholder_anthropic')
    : t('settings.llm.provider.base_url_placeholder_openai'),
)

// ─── 未保存守卫 (prompt / llm 表单) ─────────────────────────────────────────
// dirty = 表单值 ≠ 基线 (最近一次服务端确认值), 不耦合 activeTab。
// 基线只在「加载成功 / 保存成功」时更新; 首次加载完成前 dirty 恒为 false。
// 注意: 本节必须位于 LLM state 声明之后 —— useUnsavedGuard 对 Ref 型 dirty
// 会立即求值 (watch immediate), getter 先于 llmProvidersLoaded 等声明执行会 TDZ。

function snapshotLlm(): string {
  return JSON.stringify({
    provider: llmProvider.value,
    api_key: llmApiKey.value,
    base_url: llmBaseUrl.value,
    model: llmModel.value,
    temperature: llmTemperature.value,
    max_tokens: llmMaxTokens.value,
    stream: llmStream.value,
  })
}

const llmSnapshot = ref('')
const llmFormDirty = computed(() => llmProvidersLoaded.value && snapshotLlm() !== llmSnapshot.value)

// banner 可见性: 当前 tab 对应的表单 dirty 时才显示
const showBanner = computed(() =>
  (activeTab.value === 'prompt' && promptFormDirty.value)
  || (activeTab.value === 'llm' && llmFormDirty.value),
)

const guard = useUnsavedGuard({
  isDirty: computed(() => promptFormDirty.value || llmFormDirty.value),
  saveAction: async () => {
    if (promptFormDirty.value) {
      const ok = await savePromptSettings()
      if (ok) toast(t('settings.prompt.saved'), 'success')
      return ok
    }
    if (llmFormDirty.value) {
      const ok = await saveLlmConfig()
      if (ok) { llmSnapshot.value = snapshotLlm() }
      return ok
    }
    return true
  },
  discardAction: async () => {
    // 守卫拦截所有离开路径, 同一时刻至多一个表单 dirty; 双分支为防御性保留
    if (promptFormDirty.value) {
      await discardPromptSettings()
    }
    if (llmFormDirty.value) {
      try { await loadLlmTab() } finally { llmSnapshot.value = snapshotLlm() }
    }
  },
  texts: () => ({
    title: t('settings.unsaved.title'),
    message: t('settings.unsaved.message'),
    confirmSave: t('common.btn.save'),
    confirmDiscard: t('settings.unsaved.discard'),
    cancel: t('settings.unsaved.cancel'),
  }),
})
guard.guardRouteLeave()

// banner 按钮: 直接走 save/discard (无守卫确认)
const guardSaveFromBanner = () => guard.save()
const guardDiscardFromBanner = () => guard.discard()

// ─── Load settings ────────────────────────────────────────────────────────────

async function loadSettings() {
  const data = await get<{ civitai_key_set?: boolean; civitai_key?: string; api_key?: string }>('/api/settings')
  if (!data) return
  if (data.civitai_key && data.civitai_key_set) civitaiKey.value = data.civitai_key
  if (data.api_key) apiKey.value = data.api_key
}

// ─── Tab switch ───────────────────────────────────────────────────────────────

async function onTabChange(next: string) {
  // 离开 prompt/llm 表单 tab 时守卫未保存更改
  if (activeTab.value === 'prompt' && next !== 'prompt' && promptFormDirty.value) {
    if (!(await guard.guardTabSwitch())) return
  }
  if (activeTab.value === 'llm' && next !== 'llm' && llmFormDirty.value) {
    if (!(await guard.guardTabSwitch())) return
  }
  activeTab.value = next
  // 守卫保证进入时必然无未保存更改, 可安全用服务端值刷新基线
  if (next === 'llm' && !llmProvidersLoaded.value) await loadLlmTab()
  if (next === 'prompt') {
    // 强制重载: 基线以服务端实际值为准, 避免其他入口改动造成快照漂移
    await loadPromptSettings(true)
  }
}

// ─── Password ─────────────────────────────────────────────────────────────────

async function changePassword() {
  if (!pwCurrent.value) { toast(t('settings.password.err_current'), 'error'); return }
  if (!pwNew.value) { toast(t('settings.password.err_new'), 'error'); return }
  if (pwNew.value.length < 4) { toast(t('settings.password.err_min_length'), 'error'); return }
  if (pwNew.value !== pwConfirm.value) { toast(t('settings.password.err_mismatch'), 'error'); return }
  pwSubmitting.value = true
  const data = await post<ApiErrorBody & { message?: string; error?: string }>('/api/settings/password', {
    current: pwCurrent.value,
    new: pwNew.value,
  })
  pwSubmitting.value = false
  if (!data) return
  if (data.error_key || data.error) {
    toast(apiErrorText(data, t('settings.password.err_current')), 'error')
  } else {
    toast(apiMessageText(data), 'success')
    pwCurrent.value = ''
    pwNew.value = ''
    pwConfirm.value = ''
  }
}

// ─── API Key ──────────────────────────────────────────────────────────────────

async function regenerateApiKey() {
  if (!await confirm({ message: t('settings.api_key.regenerate_confirm') })) return
  regenLoading.value = true
  const data = await post<{ ok?: boolean; api_key?: string; error?: string }>('/api/settings/api-key', {})
  regenLoading.value = false
  if (!data) return
  if (data.ok && data.api_key) {
    apiKey.value = data.api_key
    apiKeyRevealed.value = true
    toast(t('settings.api_key.regenerated'), 'success')
  } else {
    toast(apiErrorText(data, t('settings.api_key.regenerate_failed')), 'error')
  }
}

// ─── CivitAI ──────────────────────────────────────────────────────────────────

async function saveCivitaiKey() {
  const key = civitaiKey.value.trim()
  if (!key) { toast(t('settings.civitai.err_empty'), 'error'); return }
  civitaiSaving.value = true
  const data = await post<{ ok?: boolean; error?: string }>('/api/settings/civitai-key', { api_key: key })
  civitaiSaving.value = false
  if (!data) return
  toast(data.ok ? t('settings.civitai.saved') : apiErrorText(data, t('settings.civitai.save_failed')), data.ok ? 'success' : 'error')
  if (data.ok) civitaiKey.value = ''
  await loadSettings()
}

async function clearCivitaiKey() {
  if (!await confirm({ message: t('settings.civitai.clear_confirm'), variant: 'danger' })) return
  const data = await post<{ ok?: boolean }>('/api/settings/civitai-key', { api_key: '' })
  if (!data?.ok) return
  toast(t('settings.civitai.cleared'), 'success')
  civitaiKey.value = ''
  await loadSettings()
}

// ─── Export / Import ──────────────────────────────────────────────────────────

async function exportConfig() {
  try {
    const res = await fetch('/api/settings/export-config')
    if (!res.ok) { toast(t('settings.config.export_failed'), 'error'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `comfycarry-config-${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast(t('settings.config.exported'), 'success')
  } catch (e: any) {
    toast(`${t('settings.config.export_failed')}: ${e.message}`, 'error')
  }
}

async function importConfig(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  ;(event.target as HTMLInputElement).value = ''
  try {
    const text = await file.text()
    const config = JSON.parse(text)
    if (!config._version) { toast(t('settings.config.invalid_format'), 'error'); return }
    if (!await confirm({ message: t('settings.config.import_confirm', { date: config._exported_at || t('settings.config.unknown_date') }) })) return
    const data = await post<{ message?: string }>('/api/settings/import-config', JSON.parse(text))
    if (!data) return
    toast(apiMessageText(data), 'success')
    await loadSettings()
  } catch (e: any) {
    toast(`${t('settings.config.import_failed')}: ${e.message}`, 'error')
  }
}

// ─── Restart / Reinitialize ───────────────────────────────────────────────────

async function restartDashboard() {
  if (!await confirm({ message: t('settings.restart_confirm') })) return
  await post('/api/settings/restart', {})
  toast(t('settings.restarting'), 'info')
  setTimeout(() => location.reload(), 3000)
}

async function reinitialize() {
  reinitKeepModels.value = true
  if (!await confirm({
    message: t('settings.reinit.confirm'),
    confirmText: t('settings.reinit.btn'),
    checkboxLabel: t('settings.reinit.keep_models'),
    checkboxDefault: true,
    checkboxRef: reinitKeepModels,
  })) return
  if (!reinitKeepModels.value && !await confirm({ message: t('settings.reinit.confirm_delete_final') })) return
  reinitLoading.value = true
  toast(t('settings.reinit.in_progress'), 'info')
  const data = await post<{ ok?: boolean; errors?: ApiErrorBody[] }>('/api/settings/reinitialize', { keep_models: reinitKeepModels.value })
  reinitLoading.value = false
  if (!data) return
  if (data.ok) {
    toast(t('settings.reinit.success'), 'success')
    setTimeout(() => location.reload(), 1500)
  } else {
    // 每步各自成败 → errors 是内嵌的 key + params 数组 (settings.py _err_item)
    const detail = (data.errors || []).map(e => apiErrorText(e)).join('; ')
    toast(`${t('settings.reinit.partial_fail')}: ${detail}`, 'error')
  }
}

// ─── LLM ─────────────────────────────────────────────────────────────────────

async function loadLlmTab() {
  const cfgData = await get<{ ok: boolean; data?: LlmConfigData }>('/api/llm/config')
  llmProvidersLoaded.value = true
  if (cfgData?.ok && cfgData.data) {
    const cfg = cfgData.data
    llmProviderKeys.value = cfg.provider_keys || {}
    if (cfg.provider) llmProvider.value = cfg.provider
    const savedProv = llmProviderKeys.value[cfg.provider || '']
    if (savedProv?.api_key) llmApiKey.value = savedProv.api_key
    if (cfg.base_url) llmBaseUrl.value = cfg.base_url
    else if (savedProv?.base_url) llmBaseUrl.value = savedProv.base_url
    if (cfg.temperature != null) llmTemperature.value = cfg.temperature
    if (cfg.max_tokens != null) llmMaxTokens.value = cfg.max_tokens
    llmStream.value = !!cfg.stream
    if (cfg.model) {
      llmModel.value = cfg.model
    }
  }
  llmSnapshot.value = snapshotLlm()
}

function onLlmProviderChange() {
  const saved = llmProviderKeys.value[llmProvider.value]
  llmApiKey.value = saved?.api_key || ''
  llmBaseUrl.value = saved?.base_url || ''
  llmAllModels.value = []
  selectedLlmModel.value = null
  if (saved?.model) {
    llmModel.value = saved.model
  } else {
    llmModel.value = ''
  }
}

function selectLlmModel(value: string | number | boolean) {
  const model = llmAllModels.value.find(m => m.id === value)
  selectedLlmModel.value = model || null
}

async function fetchLlmModels() {
  if (!llmProvider.value) { toast(t('settings.llm.err_no_provider'), 'error'); return }
  if (!llmApiKey.value) { toast(t('settings.llm.err_no_key'), 'error'); return }
  llmFetchingModels.value = true
  const data = await post<{ ok?: boolean; models?: ModelOption[]; error?: string }>('/api/llm/models', {
    provider: llmProvider.value,
    api_key: llmApiKey.value,
    base_url: llmBaseUrl.value,
  })
  llmFetchingModels.value = false
  if (!data?.ok) {
    toast(apiErrorText(data, t('settings.llm.model.fetch_failed')), 'error')
    return
  }
  const models = (data.models || []).sort((a, b) => {
    const na = (a.name || a.id || '').toLowerCase()
    const nb = (b.name || b.id || '').toLowerCase()
    return na.localeCompare(nb)
  })
  llmAllModels.value = models
  if (llmModel.value) {
    selectedLlmModel.value = models.find(model => model.id === llmModel.value) || null
  } else if (models.length > 0) {
    const first = models[0]
    llmModel.value = first.id
    selectedLlmModel.value = first
  }
  toast(t('settings.llm.model.fetched_count', { count: models.length }), 'success')
}

async function saveLlmConfig(): Promise<boolean> {
  if (!llmProvider.value) { toast(t('settings.llm.err_no_provider'), 'error'); return false }
  if (!llmApiKey.value) { toast(t('settings.llm.err_no_key'), 'error'); return false }
  llmSaving.value = true
  const body: Record<string, unknown> = {
    provider: llmProvider.value,
    api_key: llmApiKey.value,
    model: llmModel.value,
    temperature: llmTemperature.value,
    max_tokens: llmMaxTokens.value,
    stream: llmStream.value,
    base_url: llmBaseUrl.value,
  }
  const data = await put<{ ok?: boolean; error?: string }>('/api/llm/config', body)
  llmSaving.value = false
  if (!data) return false
  if (data.ok) {
    llmProviderKeys.value[llmProvider.value] = {
      ...llmProviderKeys.value[llmProvider.value],
      api_key: llmApiKey.value,
      model: llmModel.value,
      base_url: llmBaseUrl.value,
    }
    toast(t('settings.llm.config_saved'), 'success')
    return true
  } else {
    toast(apiErrorText(data, t('settings.llm.save_failed')), 'error')
    return false
  }
}

async function testLlmConnection() {
  if (!llmProvider.value) { toast(t('settings.llm.err_no_provider'), 'error'); return }
  if (!llmApiKey.value) { toast(t('settings.llm.err_no_key'), 'error'); return }
  if (!llmModel.value) { toast(t('settings.llm.err_no_model'), 'error'); return }
  llmTesting.value = true
  llmTestResult.value = null
  const data = await post<{ ok?: boolean; latency_ms?: number; response?: string; error?: string }>('/api/llm/test', {
    provider: llmProvider.value,
    api_key: llmApiKey.value,
    model: llmModel.value,
    base_url: llmBaseUrl.value,
  })
  llmTesting.value = false
  if (!data) return
  if (data.ok) {
    const extra = [data.latency_ms ? `${data.latency_ms}ms` : '', data.response ? `— ${data.response}` : ''].filter(Boolean).join(' ')
    llmTestResult.value = { ok: true, message: `✓ ${t('settings.llm.test_success')}${extra ? ' ' + extra : ''}` }
  } else {
    llmTestResult.value = { ok: false, message: `✗ ${t('settings.llm.test_failed')}: ${apiErrorText(data, t('settings.llm.unknown_error'))}` }
  }
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────

loadSettings()
</script>

<template>
  <div class="settings-page">
    <div class="page-body">
      <TabSwitcher :title="t('settings.title')" :tabs="tabs" :model-value="activeTab" @update:model-value="onTabChange" />

      <!-- 未保存守卫 banner (prompt/llm 表单 dirty 时显示) -->
      <UnsavedBanner
        :visible="showBanner"
        :message="t('settings.unsaved.message_banner')"
        :save-label="t('common.btn.save')"
        :discard-label="t('settings.unsaved.discard')"
        :saving="promptSaving || llmSaving"
        @save="guardSaveFromBanner"
        @discard="guardDiscardFromBanner"
      />

      <!-- ═══ Tab: ComfyCarry ═══════════════════════════════ -->
      <div v-show="activeTab === 'comfycarry'" class="tab-panel settings-centered">
          <!-- Password -->
          <BaseCard density="roomy">
            <h3 class="settings-card-title">
              <MsIcon name="lock" />
              {{ t('settings.password.title') }}
            </h3>
            <form @submit.prevent="changePassword" autocomplete="off">
              <input
                type="text"
                name="username"
                autocomplete="username"
                tabindex="-1"
                aria-hidden="true"
                style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0"
              />
              <FormField :label="t('settings.password.current')">
                <SecretInput
                  v-model="pwCurrent"
                  is-password
                  :placeholder="t('settings.password.current_placeholder')"
                  autocomplete="current-password"
                  input-class="form-input"
                />
              </FormField>
              <FormField :label="t('settings.password.new')">
                <SecretInput
                  v-model="pwNew"
                  is-password
                  :placeholder="t('settings.password.new_placeholder')"
                  autocomplete="new-password"
                  input-class="form-input"
                />
              </FormField>
              <FormField :label="t('settings.password.confirm')">
                <SecretInput
                  v-model="pwConfirm"
                  is-password
                  :placeholder="t('settings.password.confirm_placeholder')"
                  autocomplete="new-password"
                  input-class="form-input"
                />
              </FormField>
              <div class="btn-row-end">
                <BaseButton type="submit" variant="primary" size="sm" :loading="pwSubmitting">
                  {{ t('settings.password.update_btn') }}
                </BaseButton>
              </div>
            </form>
          </BaseCard>

          <!-- API Key -->
          <BaseCard density="roomy">
            <h3 class="settings-card-title">
              <MsIcon name="key" />
              ComfyCarry API Key
              <HelpTip :text="t('settings.api_key.help')" />
            </h3>
            <SecretInput
              v-model="apiKey"
              v-model:revealed="apiKeyRevealed"
              readonly
              copyable
              input-class="form-input mono-input"
              style="margin-bottom:12px"
            />
            <div class="btn-row-end">
              <BaseButton variant="primary" size="sm" :loading="regenLoading" @click="regenerateApiKey">
                {{ t('settings.api_key.regenerate') }}
              </BaseButton>
            </div>
          </BaseCard>

          <!-- Export / Import -->
          <BaseCard density="roomy">
            <h3 class="settings-card-title">
              <MsIcon name="package_2" />
              {{ t('settings.config.title') }}
            </h3>
            <div class="settings-action-list">
              <div class="settings-action-row">
                <p class="settings-action-copy">{{ t('settings.config.export_desc') }}</p>
                <BaseButton variant="primary" size="sm" @click="exportConfig">
                  <MsIcon name="download" />
                  {{ t('settings.config.export_btn') }}
                </BaseButton>
              </div>
              <div class="settings-action-row">
                <p class="settings-action-copy">{{ t('settings.config.import_desc') }}</p>
                <BaseButton variant="primary" size="sm" @click="($refs.importFileInput as HTMLInputElement)?.click()">
                  <MsIcon name="upload" />
                  {{ t('settings.config.import_btn') }}
                </BaseButton>
                <input ref="importFileInput" type="file" accept=".json" @change="importConfig" style="display:none" />
              </div>
            </div>
          </BaseCard>

          <!-- Maintenance -->
          <BaseCard density="roomy">
            <h3 class="settings-card-title">
              <MsIcon name="build" />
              {{ t('settings.maintenance.title') }}
            </h3>
            <div class="settings-action-list">
              <div class="settings-action-row">
                <p class="settings-action-copy">{{ t('settings.maintenance.restart_desc') }}</p>
                <BaseButton variant="primary" size="sm" @click="restartDashboard">
                  {{ t('settings.restart_btn') }}
                </BaseButton>
              </div>
              <div class="settings-action-row">
                <p class="settings-action-copy">{{ t('settings.maintenance.reinit_desc') }}</p>
                <BaseButton variant="primary" size="sm" :loading="reinitLoading" @click="reinitialize">
                  {{ t('settings.reinit.btn') }}
                </BaseButton>
              </div>
            </div>
          </BaseCard>

          <!-- About -->
          <BaseCard density="roomy" radius="lg" class="about-card">
            <section class="about-content" aria-labelledby="about-product-name">
              <header class="about-identity">
                <img class="about-logo" src="/logo-tile.svg" alt="" aria-hidden="true" />
                <h3 id="about-product-name" class="about-product-name">ComfyCarry</h3>
                <div class="about-build">
                  <span>{{ t('settings.about.version') }} {{ app.version || '—' }}</span>
                  <span class="about-meta-sep" aria-hidden="true">·</span>
                  <code>{{ (app.commit || '').substring(0, 8) || '—' }}</code>
                </div>
              </header>

              <p class="about-desc">{{ t('settings.about.desc') }}</p>

              <div class="about-update-block">
                <div class="about-actions">
                  <BaseButton
                    variant="primary"
                    size="sm"
                    :disabled="updateChecking || updateApplying"
                    :loading="updateChecking || updateApplying"
                    :aria-label="updateActionLabel"
                    @click="runUpdateAction"
                  >
                    {{ updateActionLabel }}
                  </BaseButton>
                </div>
                <div
                  class="about-update-status"
                  aria-live="polite"
                  :aria-busy="updateChecking || updateApplying"
                >
                  <template v-if="updateChecking || updateApplying">
                    <span>{{ updateApplying ? updatePhase : t('settings.update.checking') }}</span>
                  </template>
                  <template v-else-if="updateInfo">
                    <StatusDot :status="updateInfo.has_update ? 'pending' : 'success'" size="sm" />
                    <span>{{ updateInfo.has_update ? t('settings.update.update_available') : t('settings.update.up_to_date') }}</span>
                    <span v-if="updateInfo.has_update && updateInfo.latest_version" class="about-update-target">
                      <span>{{ updateInfo.latest_version }}</span>
                    </span>
                  </template>
                </div>
              </div>

              <footer class="about-project" :aria-label="t('settings.about.project_info')">
                <p class="about-project-label">{{ t('settings.about.project_info') }}</p>
                <div class="about-project-links">
                  <a class="about-project-link" :href="repoUrl" target="_blank" rel="noopener noreferrer">
                    <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" /></svg>
                    <span>{{ t('settings.about.github') }}</span>
                  </a>
                  <a class="about-project-link" :href="dockerHubUrl" target="_blank" rel="noopener noreferrer">
                    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.983 11.078h2.119a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.119a.185.185 0 0 0-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 0 0 .186-.186V3.574a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 0 0 .186-.186V6.29a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 0 0 .184-.186V6.29a.185.185 0 0 0-.185-.185H8.1a.185.185 0 0 0-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 0 0 .185-.186V6.29a.185.185 0 0 0-.185-.185H5.136a.186.186 0 0 0-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 0 0 .185-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.186.186 0 0 0-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 0 0-.75.748 11.376 11.376 0 0 0 .692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 0 0 3.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z" /></svg>
                    <span>{{ t('settings.about.dockerhub') }}</span>
                  </a>
                </div>
                <p class="about-credit">
                  {{ t('settings.about.credit_prefix') }}<a class="about-author" :href="erocraftUrl" target="_blank" rel="noopener noreferrer" lang="zh-CN">艾萝工坊</a>{{ t('settings.about.credit_suffix') }}
                </p>
                <p class="about-copyright" lang="en">© {{ copyrightRange }} Erocraft</p>
              </footer>
            </section>
          </BaseCard>
      </div>

      <!-- ═══ Tab: Prompt Editor ═══════════════════════════ -->
      <div v-show="activeTab === 'prompt'" class="tab-panel settings-centered">
        <!-- 翻译设置 -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="translate" />
            {{ t('settings.prompt.translation.title') }}
          </h3>
          <FormField :label="t('settings.prompt.translation.show')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.show_translation" />
          </FormField>
          <FormField :label="t('settings.prompt.translation.provider')" density="compact">
            <BaseSelect
              v-model="promptSettings.translate_provider"
              :options="translateProviderOptions"
              :disabled="!promptSettings.show_translation"
            />
          </FormField>
        </BaseCard>

        <!-- 规格化设置 -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title" style="margin-bottom:14px">
            <MsIcon name="auto_fix_high" />
            {{ t('settings.prompt.normalize.title') }}
            <span style="margin-left:auto">
              <ToggleSwitch :model-value="normalizeEnabled" @update:model-value="toggleNormalizeAll" />
            </span>
          </h3>
          <FormField :label="t('settings.prompt.normalize.comma')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.normalize_comma" :disabled="!normalizeEnabled" />
          </FormField>
          <FormField :label="t('settings.prompt.normalize.period')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.normalize_period" :disabled="!normalizeEnabled" />
          </FormField>
          <FormField :label="t('settings.prompt.normalize.bracket')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.normalize_bracket" :disabled="!normalizeEnabled" />
          </FormField>
          <FormField :label="t('settings.prompt.normalize.underscore')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.normalize_underscore" :disabled="!normalizeEnabled" />
          </FormField>
          <FormField :label="t('settings.prompt.normalize.escape_bracket')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.escape_bracket" :disabled="!normalizeEnabled" />
          </FormField>
        </BaseCard>

        <!-- 自动补全设置 -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="auto_awesome" />
            {{ t('settings.prompt.autocomplete.title') }}
          </h3>
          <FormField :label="t('settings.prompt.autocomplete.limit')" density="compact">
            <BaseSelect
              v-model="promptSettings.autocomplete_limit"
              :options="promptAutocompleteOptions"
            />
          </FormField>
        </BaseCard>

        <!-- 标签库设置 -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="category" />
            {{ t('settings.prompt.tag_library.title') }}
          </h3>
          <FormField :label="t('settings.prompt.tag_library.show_nsfw')" layout="horizontal" density="compact">
            <ToggleSwitch v-model="promptSettings.show_nsfw" />
          </FormField>
        </BaseCard>
      </div>

      <!-- ═══ Tab: CivitAI ═══════════════════════════════ -->
      <div v-show="activeTab === 'civitai'" class="tab-panel settings-centered">
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="palette" />
            CivitAI API Key
          </h3>
          <FormField>
            <template #label>
              {{ t('settings.civitai.key_prefix') }}
              <a href="https://civitai.com/user/account" target="_blank" style="color:var(--ac)">{{ t('settings.civitai.key_link') }}</a>
              {{ t('settings.civitai.key_suffix') }}
            </template>
            <SecretInput
              v-model="civitaiKey"
              :placeholder="t('settings.civitai.placeholder')"
              autocomplete="off"
              input-class="form-input"
            />
          </FormField>
          <div style="display:flex;gap:8px;justify-content:flex-end">
            <BaseButton variant="primary" size="sm" :loading="civitaiSaving" @click="saveCivitaiKey">
              <MsIcon v-if="!civitaiSaving" name="save" />
              {{ t('common.btn.save') }}
            </BaseButton>
            <BaseButton variant="danger" size="sm" square :title="t('common.btn.clear')" @click="clearCivitaiKey">
              <MsIcon name="delete" />
            </BaseButton>
          </div>
        </BaseCard>
      </div>

      <!-- ═══ Tab: LLM ═══════════════════════════════ -->
      <div v-show="activeTab === 'llm'" class="tab-panel settings-centered">
        <!-- Provider & Model (合并卡片) -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="smart_toy" />
            {{ t('settings.llm.provider.title') }}
            <HelpTip :text="t('settings.llm.provider.help')" />
          </h3>
          <FormField :label="t('settings.llm.provider.label')" density="compact">
            <BaseSelect v-model="llmProvider" :options="llmProviderOptions" :placeholder="t('settings.llm.provider.select_placeholder')" @change="onLlmProviderChange" />
          </FormField>
          <FormField v-if="showLlmBaseUrl" density="compact">
            <template #label>
              {{ t('settings.llm.provider.base_url') }}
              <HelpTip :text="llmBaseUrlHelp" />
            </template>
            <input type="url" v-model="llmBaseUrl" class="form-input" :placeholder="llmBaseUrlPlaceholder" />
          </FormField>
          <FormField :label="t('settings.llm.provider.api_key')" density="compact">
            <SecretInput
              v-model="llmApiKey"
              :placeholder="t('settings.llm.provider.api_key_placeholder')"
              autocomplete="off"
              input-class="form-input"
            />
          </FormField>
          <FormField :label="t('settings.llm.model.label')" :hint="llmModelInfo" density="compact">
            <FieldControlRow>
              <BaseSelect
                v-model="llmModel"
                :options="llmModelSelectOptions"
                searchable
                allow-custom
                :placeholder="t('settings.llm.model.input_placeholder')"
                :search-placeholder="t('settings.llm.model.search_placeholder')"
                :empty-text="t('settings.llm.model.no_match')"
                @change="selectLlmModel"
              />
              <BaseButton size="sm" :disabled="llmFetchingModels" :loading="llmFetchingModels" :title="t('settings.llm.model.fetch_title')" @click="fetchLlmModels">
                <MsIcon v-if="!llmFetchingModels" name="refresh" color="var(--ac)" />
              </BaseButton>
            </FieldControlRow>
          </FormField>
          <!-- 测试连接 (合并卡片内) -->
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px;padding-top:12px;border-top:1px solid var(--bd)">
            <span
              v-if="llmTestResult"
              style="font-size:.85rem;margin-right:auto"
              :style="{ color: llmTestResult.ok ? 'var(--green)' : 'var(--red)' }"
            >
              {{ llmTestResult.message }}
            </span>
            <span v-else style="margin-right:auto"></span>
            <BaseButton size="sm" :loading="llmTesting" @click="testLlmConnection">
              <MsIcon v-if="!llmTesting" name="wifi_tethering" />
              {{ t('settings.llm.test_btn') }}
            </BaseButton>
          </div>
        </BaseCard>

        <!-- Parameters -->
        <BaseCard density="roomy">
          <h3 class="settings-card-title">
            <MsIcon name="tune" />
            {{ t('settings.llm.params.title') }}
          </h3>
          <FormField density="compact">
            <template #label>
              {{ t('settings.llm.params.temperature') }}
              <HelpTip :text="t('settings.llm.params.temperature_help')" />
            </template>
            <template #label-right>{{ llmTemperature.toFixed(1) }}</template>
            <input type="range" v-model.number="llmTemperature" min="0" max="2" step="0.1" class="form-range" />
            <template #below>
              <div class="gen-range-tips"><span>0</span><span>1</span><span>2</span></div>
            </template>
          </FormField>
          <FormField density="compact">
            <template #label>
              {{ t('settings.llm.params.max_tokens') }}
              <HelpTip :text="t('settings.llm.params.max_tokens_help')" />
            </template>
            <template #label-right>{{ llmMaxTokens }}</template>
            <input type="range" v-model.number="llmMaxTokens" min="100" max="16000" step="100" class="form-range" />
            <template #below>
              <div class="gen-range-tips"><span>100</span><span>4000</span><span>8000</span><span>16000</span></div>
            </template>
          </FormField>
          <FormField density="compact">
            <template #label>
              {{ t('settings.llm.params.stream') }}
              <HelpTip :text="t('settings.llm.params.stream_help')" />
            </template>
            <template #label-right>
              <ToggleSwitch v-model="llmStream" />
            </template>
          </FormField>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Vue-unique: page wrapper */
.settings-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Vue-unique: button row align right */
.btn-row-end {
  display: flex;
  justify-content: flex-end;
}

/* Vue-unique: centered settings-tab layout */
.settings-centered {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 760px;
  margin: 8px auto 0;
}

/* Vue-unique: card heading inside settings */
.settings-card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .92rem;
  font-weight: 600;
  margin: 0 0 14px;
}

/* Vue-unique: settings rows with copy left and a standard action right */
.settings-action-list {
  display: flex;
  flex-direction: column;
}
.settings-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  min-width: 0;
  padding: var(--sp-3) 0;
}
.settings-action-row:first-child {
  padding-top: 0;
}
.settings-action-row:last-child {
  padding-bottom: 0;
}
.settings-action-copy {
  min-width: 0;
  margin: 0;
  color: var(--t2);
  font-size: .82rem;
  line-height: 1.5;
}
.settings-action-row > :deep(.base-btn) {
  flex-shrink: 0;
}

/* Vue-unique: centered About identity block */
.about-card {
  --card-py-roomy: clamp(28px, 5vw, 42px);
  --card-px-roomy: clamp(20px, 6vw, 48px);
}
.about-content {
  text-align: center;
}
.about-logo {
  display: block;
  width: 60px;
  height: 60px;
  margin: 0 auto 14px;
  border-radius: 14px;
  box-shadow: 0 7px 18px color-mix(in srgb, var(--ac) 24%, transparent);
}
.about-product-name {
  margin: 0;
  color: var(--t1);
  font-size: 1.32rem;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -.015em;
}
.about-build {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 7px;
  color: var(--t2);
  font-size: .76rem;
  line-height: 1.5;
}
.about-build code {
  padding: 1px 5px;
  border-radius: var(--r-xs);
  background: var(--bg2);
  color: var(--t2);
  font-family: 'IBM Plex Mono', monospace;
  font-size: .7rem;
}
.about-meta-sep {
  color: var(--t3);
}
.about-desc {
  max-width: 50ch;
  margin: 17px auto 0;
  color: var(--t2);
  font-size: .86rem;
  line-height: 1.7;
}
.about-update-block {
  margin-top: 20px;
}
.about-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.about-update-status {
  display: flex;
  min-height: 1.5em;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
  flex-wrap: wrap;
  color: var(--t2);
  font-size: .76rem;
  line-height: 1.5;
}
.about-update-target {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--t3);
}
.about-project {
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid var(--bd);
}
.about-project-label {
  margin: 0 0 11px;
  color: var(--t3);
  font-size: .72rem;
  font-weight: 600;
  letter-spacing: .06em;
}
.about-project-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px 18px;
  flex-wrap: wrap;
}
.about-project-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ac);
  font-size: .79rem;
  font-weight: 500;
  text-decoration: none;
}
.about-project-link:hover,
.about-author:hover {
  color: var(--ac2);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.about-project-link svg {
  width: 15px;
  height: 15px;
  flex: none;
}
.about-credit {
  margin: 14px 0 0;
  color: var(--t2);
  font-size: .76rem;
  line-height: 1.55;
}
.about-author {
  color: inherit;
  font-weight: 600;
  text-decoration: none;
}
.about-copyright {
  margin: 3px 0 0;
  color: var(--t3);
  font-size: .72rem;
  line-height: 1.5;
}

@media (max-width: 520px) {
  .settings-action-row {
    align-items: flex-start;
    gap: var(--sp-3);
  }
  .settings-action-copy {
    padding-top: 3px;
  }
  .about-card {
    --card-py-roomy: 28px;
    --card-px-roomy: 18px;
  }
}

/* Vue-unique: mono variant for API key display */
.mono-input {
  font-family: 'IBM Plex Mono', monospace;
  font-size: .82rem;
  letter-spacing: .5px;
  padding-right: 72px;
}

/* Vue-unique: LLM range slider tick marks */
.gen-range-tips {
  display: flex;
  justify-content: space-between;
  font-size: .72rem;
  color: var(--t3);
  margin-top: 2px;
}
</style>
