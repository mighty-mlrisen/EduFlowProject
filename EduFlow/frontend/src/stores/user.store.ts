import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as userApi from '@/api/user.api'
import type { ProfileResponse, ProfileUpdateRequest } from '@/types/user.types'

export const useUserStore = defineStore('user', () => {
  const myProfile = ref<ProfileResponse | null>(null)
  const viewedProfile = ref<ProfileResponse | null>(null)
  const subscribers = ref<ProfileResponse[]>([])
  const subscriptions = ref<ProfileResponse[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchMyProfile() {
    loading.value = true
    error.value = null
    try {
      myProfile.value = await userApi.getMyProfile()
    } catch (e) {
      error.value = 'Не удалось загрузить профиль'
    } finally {
      loading.value = false
    }
  }

  async function fetchProfileById(userId: number) {
    loading.value = true
    error.value = null
    try {
      viewedProfile.value = await userApi.getProfileById(userId)
    } catch (e) {
      error.value = 'Пользователь не найден'
    } finally {
      loading.value = false
    }
  }

  async function updateMyProfile(payload: ProfileUpdateRequest) {
    loading.value = true
    error.value = null
    try {
      myProfile.value = await userApi.updateProfile(payload)
    } finally {
      loading.value = false
    }
  }

  async function toggleSubscription(userId: number, status: boolean) {
    const updated = await userApi.subscribe(userId, status)
    if (viewedProfile.value?.userId === userId) {
      viewedProfile.value = updated
    }
    return updated
  }

  async function fetchMySubscribers() {
    subscribers.value = await userApi.getMySubscribers()
  }

  async function fetchMySubscriptions() {
    subscriptions.value = await userApi.getMySubscriptions()
  }

  return {
    myProfile,
    viewedProfile,
    subscribers,
    subscriptions,
    loading,
    error,
    fetchMyProfile,
    fetchProfileById,
    updateMyProfile,
    toggleSubscription,
    fetchMySubscribers,
    fetchMySubscriptions
  }
})
