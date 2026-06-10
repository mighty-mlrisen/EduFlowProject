<script setup lang="ts">
import { ref, watch } from 'vue'
import { subscribe } from '@/api/user.api'

const props = defineProps<{ userId: number; subscribed: boolean }>()

const isSubscribed = ref(props.subscribed)
const loading = ref(false)
const hovered = ref(false)

watch(() => props.subscribed, (v) => { isSubscribed.value = v })

async function toggle(e: MouseEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (loading.value) return
  loading.value = true
  try {
    const result = await subscribe(props.userId, !isSubscribed.value)
    isSubscribed.value = result.statusSubscribtion
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button
    @click="toggle"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    class="px-4 py-1.5 text-sm font-medium rounded-full border transition-all duration-300 flex items-center gap-1.5 overflow-hidden"
    :class="isSubscribed
      ? 'border-gray-300 text-gray-600 bg-white hover:border-red-300 hover:text-red-400 hover:bg-red-50'
      : 'border-blue-500 text-blue-600 bg-white hover:bg-blue-50'"
  >
    <svg v-if="loading" class="w-3.5 h-3.5 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
    <template v-else>
      <Transition name="label" mode="out-in">
        <span v-if="!isSubscribed" key="sub">Подписаться</span>
        <span v-else-if="hovered" key="unsub">Отписаться</span>
        <span v-else key="subd">Подписан</span>
      </Transition>
    </template>
  </button>
</template>

<style scoped>
.label-enter-active,
.label-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.label-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.label-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
