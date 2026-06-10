import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { signIn, signUp } from '@/api/auth.api'
import type { JwtResponse, AuthRequest, SignUpRequest } from '@/types/auth.types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<JwtResponse | null>(
    JSON.parse(localStorage.getItem('user') ?? 'null')
  )

  const isAuthenticated = computed(() => !!user.value?.accessToken)
  const currentUserId = computed(() => user.value?.id ?? null)
  const currentUserRole = computed(() => user.value?.role ?? null)

  function setUser(data: JwtResponse) {
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
    localStorage.setItem('accessToken', data.accessToken)
    localStorage.setItem('refreshToken', data.refreshToken)
  }

  function clearUser() {
    user.value = null
    localStorage.removeItem('user')
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }

  async function login(credentials: AuthRequest): Promise<void> {
    const data = await signIn(credentials)
    setUser(data)
  }

  async function register(payload: SignUpRequest): Promise<void> {
    const data = await signUp(payload)
    setUser(data)
  }

  function logout() {
    clearUser()
  }

  return {
    user,
    isAuthenticated,
    currentUserId,
    currentUserRole,
    login,
    register,
    logout,
    setUser,
    clearUser
  }
})
