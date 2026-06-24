import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to) {
    const name = String(to.name)
    const keyMap: Record<string, string> = {
      'feed': 'feed:scroll',
      'subscription-feed': 'subfeed:scroll',
      'publish': 'publish:scroll',
      'saved': 'saved:scroll',
      'my-profile': 'my-profile:scroll',
    }
    const key = name === 'category'
      ? `category-${to.params.id}:scroll`
      : name === 'profile'
      ? `profile-${to.params.id}:scroll`
      : keyMap[name]
    if (key && sessionStorage.getItem(key)) return false
    return { top: 0 }
  },
  routes: [
    // --- Публичные ---
    {
      path: '/',
      name: 'feed',
      component: () => import('@/views/feed/FeedView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresGuest: true }
    },

    // --- Защищённые ---
    {
      path: '/profile',
      name: 'my-profile',
      component: () => import('@/views/profile/MyProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile/:id',
      name: 'profile',
      component: () => import('@/views/profile/ProfileView.vue'),
      props: (route) => ({ userId: Number(route.params.id) }),
      meta: { requiresAuth: true }
    },
    {
      path: '/feed',
      name: 'subscription-feed',
      component: () => import('@/views/feed/SubscriptionFeedView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/publish',
      name: 'publish',
      component: () => import('@/views/publish/PublishView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/article/:id',
      name: 'article',
      component: () => import('@/views/article/ArticleView.vue'),
      props: (route) => ({ articleId: Number(route.params.id) }),
      meta: { requiresAuth: true }
    },
    {
      path: '/category/:id',
      name: 'category',
      component: () => import('@/views/feed/CategoryView.vue'),
      props: (route) => ({ categoryId: Number(route.params.id) }),
      meta: { requiresAuth: true }
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/feed/SearchView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/saved',
      name: 'saved',
      component: () => import('@/views/saved/SavedArticlesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/stats',
      name: 'stats',
      component: () => import('@/views/stats/StatsView.vue'),
      meta: { requiresAuth: true }
    },

    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresGuest && auth.isAuthenticated) {
    return { name: 'feed' }
  }
})

export default router
