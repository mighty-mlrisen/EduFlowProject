<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ login: '', password: '' })
const loading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!form.login.trim() || !form.password.trim()) {
    error.value = 'Заполните все поля'
    return
  }
  loading.value = true
  error.value = null
  try {
    await auth.login({ login: form.login.trim(), password: form.password })
    const redirect = route.query.redirect as string | undefined
    router.push(redirect ?? { name: 'feed' })
  } catch {
    // Бэкенд возвращает 500 при неверных учётных данных — показываем понятное сообщение
    error.value = 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-3.5rem)] px-4">
    <div class="w-full max-w-sm">

      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Вход</h1>
        <p class="text-sm text-gray-500 mb-6">
          Нет аккаунта?
          <RouterLink to="/register" class="text-blue-600 hover:underline font-medium">
            Зарегистрироваться
          </RouterLink>
        </p>

        <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">

          <!-- Логин -->
          <div class="flex flex-col gap-1">
            <label for="login" class="text-sm font-medium text-gray-700">Логин</label>
            <input
              id="login"
              v-model="form.login"
              type="text"
              autocomplete="username"
              placeholder="your@email.com"
              :disabled="loading"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm outline-none
                     focus:border-blue-500 focus:ring-2 focus:ring-blue-100
                     disabled:bg-gray-50 disabled:text-gray-400 transition"
            />
          </div>

          <!-- Пароль -->
          <div class="flex flex-col gap-1">
            <label for="password" class="text-sm font-medium text-gray-700">Пароль</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              :disabled="loading"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm outline-none
                     focus:border-blue-500 focus:ring-2 focus:ring-blue-100
                     disabled:bg-gray-50 disabled:text-gray-400 transition"
            />
          </div>

          <!-- Ошибка -->
          <p v-if="error" class="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg">
            {{ error }}
          </p>

          <!-- Кнопка -->
          <button
            type="submit"
            :disabled="loading"
            class="mt-1 w-full py-2.5 bg-blue-600 text-white font-medium text-sm rounded-lg
                   hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading">Входим...</span>
            <span v-else>Войти</span>
          </button>

        </form>
      </div>

    </div>
  </div>
</template>
