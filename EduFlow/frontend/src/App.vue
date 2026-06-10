<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import { useThemeStore } from '@/stores/theme.store'

useThemeStore()
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <AppHeader />
    <main class="flex-1">
      <RouterView />
    </main>
  </div>
</template>
