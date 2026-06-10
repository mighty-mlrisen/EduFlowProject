<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({
  login: '',
  password: '',
  passwordConfirm: '',
  username: ''
})

const loading = ref(false)
const error = ref<string | null>(null)
const passwordTouched = ref(false)

// --- Требования к паролю ---
const passwordRules = computed(() => [
  { label: 'Минимум 8 символов',       met: form.password.length >= 8 },
  { label: 'Заглавная буква (A–Z)',     met: /[A-Z]/.test(form.password) },
  { label: 'Цифра (0–9)',               met: /[0-9]/.test(form.password) },
  { label: 'Спецсимвол (!@#$%^&*...)', met: /[^A-Za-z0-9]/.test(form.password) }
])

const isPasswordValid = computed(() => passwordRules.value.every(r => r.met))

function mapServerError(message: string | undefined): string {
  if (!message) return 'Ошибка при регистрации'
  if (message.toLowerCase().includes('already taken')) return 'Этот логин уже занят'
  return 'Ошибка при регистрации'
}

async function handleSubmit() {
  error.value = null

  if (!form.login.trim() || !form.username.trim()) {
    error.value = 'Заполните все обязательные поля'
    return
  }
  if (!isPasswordValid.value) {
    error.value = 'Пароль не соответствует требованиям'
    return
  }
  if (form.password !== form.passwordConfirm) {
    error.value = 'Пароли не совпадают'
    return
  }

  loading.value = true
  try {
    await auth.register({
      login: form.login.trim(),
      password: form.password,
      username: form.username.trim(),
      userRole: 'ROLE_USER'
    })
    router.push({ name: 'feed' })
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    error.value = mapServerError(err?.response?.data?.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-3.5rem)] px-4 py-8">
    <div class="w-full max-w-sm">

      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-1">Регистрация</h1>
        <p class="text-sm text-gray-500 mb-6">
          Уже есть аккаунт?
          <RouterLink to="/login" class="text-blue-600 hover:underline font-medium">
            Войти
          </RouterLink>
        </p>

        <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">

          <!-- Логин -->
          <div class="flex flex-col gap-1">
            <label for="reg-login" class="text-sm font-medium text-gray-700">
              Логин <span class="text-red-400">*</span>
            </label>
            <input
              id="reg-login"
              v-model="form.login"
              type="text"
              autocomplete="username"
              placeholder="your@email.com"
              :disabled="loading"
              class="input-field"
            />
          </div>

          <!-- Отображаемое имя -->
          <div class="flex flex-col gap-1">
            <label for="reg-username" class="text-sm font-medium text-gray-700">
              Имя <span class="text-red-400">*</span>
            </label>
            <input
              id="reg-username"
              v-model="form.username"
              type="text"
              autocomplete="name"
              placeholder="Иван Иванов"
              :disabled="loading"
              class="input-field"
            />
          </div>

          <!-- Пароль -->
          <div class="flex flex-col gap-1">
            <label for="reg-password" class="text-sm font-medium text-gray-700">
              Пароль <span class="text-red-400">*</span>
            </label>
            <input
              id="reg-password"
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              placeholder="Введите пароль"
              :disabled="loading"
              @focus="passwordTouched = true"
              class="input-field"
              :class="passwordTouched && form.password && !isPasswordValid
                ? 'border-red-300 focus:border-red-400 focus:ring-red-100'
                : ''"
            />

            <!-- Требования к паролю -->
            <div v-if="passwordTouched && form.password" class="mt-1.5 flex flex-col gap-1">
              <div
                v-for="rule in passwordRules"
                :key="rule.label"
                class="flex items-center gap-1.5 text-xs"
                :class="rule.met ? 'text-green-600' : 'text-gray-400'"
              >
                <svg v-if="rule.met" class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clip-rule="evenodd"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="9" stroke-width="2"/>
                </svg>
                {{ rule.label }}
              </div>
            </div>
          </div>

          <!-- Повтор пароля -->
          <div class="flex flex-col gap-1">
            <label for="reg-password-confirm" class="text-sm font-medium text-gray-700">
              Повторите пароль <span class="text-red-400">*</span>
            </label>
            <input
              id="reg-password-confirm"
              v-model="form.passwordConfirm"
              type="password"
              autocomplete="new-password"
              placeholder="••••••••"
              :disabled="loading"
              class="input-field"
              :class="form.passwordConfirm && form.password !== form.passwordConfirm
                ? 'border-red-300 focus:border-red-400 focus:ring-red-100'
                : ''"
            />
            <p
              v-if="form.passwordConfirm && form.password !== form.passwordConfirm"
              class="text-xs text-red-500 mt-0.5"
            >
              Пароли не совпадают
            </p>
          </div>

          <!-- Ошибка сервера -->
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
            <span v-if="loading">Регистрируемся...</span>
            <span v-else>Создать аккаунт</span>
          </button>

        </form>
      </div>

    </div>
  </div>
</template>

<style scoped>
.input-field {
  @apply w-full px-3 py-2 rounded-lg border border-gray-300 text-sm outline-none
         focus:border-blue-500 focus:ring-2 focus:ring-blue-100
         disabled:bg-gray-50 disabled:text-gray-400 transition bg-white;
}
</style>
