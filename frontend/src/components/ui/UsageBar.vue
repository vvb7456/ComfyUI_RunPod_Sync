<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ name: 'UsageBar' })

const props = withDefaults(defineProps<{
  percent: number
  baseColor?: string
  height?: number
}>(), {
  baseColor: 'var(--ac)',
  height: 5,
})

const clampedPercent = computed(() => {
  const value = Number.isFinite(props.percent) ? props.percent : 0
  return Math.max(0, Math.min(100, value))
})

const barStyle = computed(() => ({
  height: `${props.height}px`,
  borderRadius: `${Math.min(props.height / 2, 6)}px`,
}))
</script>

<template>
  <div
    class="usage-bar"
    :style="barStyle"
    :aria-valuenow="Math.round(clampedPercent)"
    aria-valuemin="0"
    aria-valuemax="100"
    role="progressbar"
  >
    <div
      class="usage-bar-fill"
      :style="{ width: clampedPercent + '%', background: baseColor, borderRadius: barStyle.borderRadius }"
    ></div>
  </div>
</template>

<style scoped>
.usage-bar {
  background: color-mix(in srgb, var(--t3) 15%, transparent);
  overflow: hidden;
  width: 100%;
}

.usage-bar-fill {
  height: 100%;
  transition: width .4s ease;
}
</style>
