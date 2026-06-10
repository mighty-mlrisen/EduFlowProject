<script setup lang="ts">
import type { SortKey } from '@/composables/useArticleSort'
import { SORT_OPTIONS } from '@/composables/useArticleSort'

defineProps<{ modelValue: SortKey }>()
defineEmits<{ (e: 'update:modelValue', val: SortKey): void }>()
</script>

<template>
  <div class="flex items-center gap-1.5 flex-wrap">
    <button
      v-for="opt in SORT_OPTIONS"
      :key="opt.value"
      @click="$emit('update:modelValue', opt.value)"
      class="px-3 py-1.5 text-sm font-medium rounded-full border transition-colors"
      :class="modelValue === opt.value
        ? 'bg-blue-600 text-white border-blue-600'
        : 'text-gray-500 border-gray-200 hover:border-blue-400 hover:text-blue-600'"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
