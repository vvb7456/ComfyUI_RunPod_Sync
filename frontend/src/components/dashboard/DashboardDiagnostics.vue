<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import MsIcon from '@/components/ui/MsIcon.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { fmtBytes } from '@/utils/format'
import type { OverviewData, ServiceEntry } from '@/types/dashboard'
import type { SystemStats } from '@/types/system'

defineOptions({ name: 'DashboardDiagnostics' })

const props = defineProps<{
  initialLoading: boolean
  data: OverviewData | null
  sysStats: SystemStats | null
  appVersion: string
  orderedServices: ServiceEntry[]
  onlineServiceCount: number
  totalServiceCount: number
}>()

const emit = defineEmits<{
  (e: 'svcAction', name: string, action: string): void
}>()

const { t } = useI18n({ useScope: 'global' })

const diagSummary = computed(() => {
  return t('dashboard.diagnostics.summary', {
    online: props.onlineServiceCount,
    total: props.totalServiceCount,
  })
})

function fmtSvcMem(bytes: number | string | undefined) {
  if (bytes === '-' || bytes === undefined || bytes === null) return '-'
  const n = Number(bytes)
  if (!n) return '-'
  return fmtBytes(n)
}

function fmtSvcCpu(cpu: number | string | undefined) {
  if (cpu === '-' || cpu === undefined || cpu === null) return '-'
  const n = Number(cpu)
  if (isNaN(n)) return '-'
  return `${n.toFixed(1)}%`
}

function fmtSvcUptime(ms: number | string | undefined) {
  if (ms === '-' || ms === undefined || ms === null) return '-'
  const n = Number(ms)
  if (!n || isNaN(n)) return '-'
  const sec = Math.floor((Date.now() - n) / 1000)
  if (sec < 0) return '-'
  if (sec < 60) return `${sec}s`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ${min % 60}m`
  const day = Math.floor(hr / 24)
  return `${day}d ${hr % 24}h`
}

function svcStatusTone(st?: string): 'running' | 'stopped' | 'loading' | 'error' {
  if (!st) return 'stopped'
  const s = st.toLowerCase()
  if (['online', 'running'].includes(s)) return 'running'
  if (['starting', 'launching', 'connecting'].includes(s)) return 'loading'
  if (['errored', 'error', 'failed'].includes(s)) return 'error'
  return 'stopped'
}

function svcStatusColor(st?: string) {
  const tone = svcStatusTone(st)
  if (tone === 'running') return 'var(--green)'
  if (tone === 'loading') return 'var(--amber)'
  if (tone === 'error') return 'var(--red)'
  return 'var(--t3)'
}
</script>

<template>
  <section class="dash-section">
    <div class="dash-section-header">
      <div class="dash-section-tagline">
        <span class="dash-accent-bar"></span>
        <span class="dash-tagline-text">{{ t('dashboard.taglines.diagnostics') }}</span>
      </div>
      <div class="dash-section-title-row">
        <h2 class="dash-section-title">{{ t('dashboard.diagnostics.title') }}</h2>
        <span class="dash-diagnostics__meta">
          {{ diagSummary }}
        </span>
      </div>
    </div>

    <!-- Initial loading for table -->
    <div v-if="initialLoading && !data" class="dash-diagnostics__loading">
      <div class="dash-spinner"></div>
      <span>{{ t('common.status.loading') }}</span>
    </div>

    <!-- Services Table -->
    <div v-else-if="data" class="dash-diagnostics-card">
      <div class="dash-svc-table-wrap">
        <table class="dash-svc-table">
          <thead>
            <tr>
              <th>{{ t('dashboard.services.name') }}</th>
              <th>{{ t('dashboard.services.status') }}</th>
              <th>{{ t('dashboard.services.uptime') }}</th>
              <th>CPU</th>
              <th>RAM</th>
              <th>{{ t('dashboard.services.restarts') }}</th>
              <th>{{ t('dashboard.services.actions_col') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="svc in orderedServices" :key="svc.name">
              <td><strong>{{ svc.name }}</strong></td>
              <td>
                <span class="dash-table-status">
                  <StatusDot :status="svcStatusTone(svc.status)" size="sm" />
                  <span :style="{ color: svcStatusColor(svc.status) }">
                    {{ svc.status || '-' }}
                  </span>
                </span>
              </td>
              <td>{{ fmtSvcUptime(svc.uptime) }}</td>
              <td>{{ fmtSvcCpu(svc.cpu) }}</td>
              <td>{{ fmtSvcMem(svc.memory) }}</td>
              <td>{{ svc.restarts ?? '-' }}</td>
              <td>
                <div class="dash-table-actions">
                  <template v-if="svc.status === 'online'">
                    <BaseButton
                      variant="danger"
                      size="xs"
                      square
                      :title="t('common.btn.stop')"
                      @click="emit('svcAction', svc.name, 'stop')"
                    >
                      <MsIcon name="stop" size="xs" />
                    </BaseButton>
                    <BaseButton
                      variant="default"
                      size="xs"
                      square
                      :title="t('common.btn.restart')"
                      @click="emit('svcAction', svc.name, 'restart')"
                    >
                      <MsIcon name="restart_alt" size="xs" />
                    </BaseButton>
                  </template>
                  <template v-else>
                    <BaseButton
                      variant="success"
                      size="xs"
                      square
                      :title="t('common.btn.start')"
                      @click="emit('svcAction', svc.name, 'start')"
                    >
                      <MsIcon name="play_arrow" size="xs" />
                    </BaseButton>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Environment Info Tags -->
      <div class="dash-env-tags">
        <span v-if="data.comfyui?.version" class="dash-env-tag">ComfyUI {{ data.comfyui.version }}</span>
        <span v-if="data.comfyui?.pytorch_version" class="dash-env-tag">PyTorch {{ data.comfyui.pytorch_version }}</span>
        <span v-if="data.comfyui?.python_version" class="dash-env-tag">Python {{ data.comfyui.python_version.split(' ')[0] }}</span>
        <span v-for="gpu in (sysStats?.gpu || [])" :key="gpu.name" class="dash-env-tag">{{ gpu.name }} {{ gpu.mem_total }}MB</span>
        <span v-if="sysStats?.cpu?.cores" class="dash-env-tag">{{ sysStats.cpu.cores }} CPU cores</span>
        <span v-if="sysStats?.memory?.total" class="dash-env-tag">{{ fmtBytes(sysStats.memory.total) }} RAM</span>
        <span v-if="appVersion" class="dash-env-tag">ComfyCarry {{ appVersion }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ── Section 4: Diagnostics & Environment ── */
.dash-diagnostics__meta {
  font-size: var(--text-xs);
  color: var(--t3);
  font-family: 'IBM Plex Mono', monospace;
}

.dash-diagnostics-card {
  background: var(--bg2);
  border: 1px solid var(--bd);
  border-radius: var(--r-md);
  overflow: hidden;
}

.dash-diagnostics__loading {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  background: var(--bg2);
  border: 1px solid var(--bd);
  border-radius: var(--r-md);
  color: var(--t3);
  font-size: var(--text-sm);
}

.dash-svc-table-wrap {
  width: 100%;
  overflow-x: auto;
}

.dash-svc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
  text-align: left;
}

.dash-svc-table th {
  padding: 10px 14px;
  font-weight: 600;
  color: var(--t3);
  border-bottom: 1px solid var(--bd);
  background: color-mix(in srgb, var(--bg3) 60%, var(--bg2));
  font-size: var(--text-xxs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.dash-svc-table td {
  padding: 10px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--bd) 60%, transparent);
  color: var(--t2);
  font-family: 'IBM Plex Mono', monospace;
  white-space: nowrap;
}

.dash-svc-table td strong {
  font-family: var(--font-sans);
  color: var(--t1);
  font-weight: 600;
}

.dash-svc-table tr:last-child td {
  border-bottom: none;
}

.dash-table-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-sans);
  font-weight: 500;
}

.dash-table-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dash-env-tags {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 12px 14px;
  background: color-mix(in srgb, var(--bg3) 40%, var(--bg2));
  border-top: 1px solid var(--bd);
  flex-wrap: wrap;
}

.dash-env-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: var(--bg1);
  border: 1px solid var(--bd);
  border-radius: var(--r-xs);
  font-size: var(--text-xxs);
  color: var(--t3);
  font-family: 'IBM Plex Mono', monospace;
}

.dash-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--bd);
  border-top-color: var(--ac);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
