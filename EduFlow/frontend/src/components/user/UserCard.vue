<script setup lang="ts">
import { computed } from 'vue'
import type { ProfileResponse } from '@/types/user.types'
import SubscribeButton from '@/components/user/SubscribeButton.vue'
import { useAuthStore } from '@/stores/auth.store'

const props = defineProps<{ profile: ProfileResponse }>()
const auth = useAuthStore()

const isOwnProfile = computed(() => auth.currentUserId === props.profile.userId)

const initials = computed(() => {
  const name = props.profile.username || props.profile.login || '?'
  return name.charAt(0).toUpperCase()
})
</script>

<template>
  <div class="flex items-center gap-4 bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow">
    <RouterLink :to="`/profile/${profile.userId}`" class="flex-shrink-0">
      <img
        v-if="profile.avatar"
        :src="profile.avatar"
        :alt="profile.username"
        class="w-12 h-12 rounded-full object-cover border border-gray-200"
      />
      <div
        v-else
        class="w-12 h-12 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xl font-bold"
      >
        {{ initials }}
      </div>
    </RouterLink>

    <div class="flex-1 min-w-0">
      <RouterLink :to="`/profile/${profile.userId}`">
        <p class="text-base font-semibold text-gray-900 hover:text-blue-600 transition-colors truncate">
          {{ profile.username || 'Без имени' }}
        </p>
      </RouterLink>
      <p class="text-sm text-gray-400 truncate">{{ profile.login }}</p>
    </div>

    <SubscribeButton
      v-if="!isOwnProfile"
      :user-id="profile.userId"
      :subscribed="profile.statusSubscribtion"
    />
  </div>
</template>
