<script setup lang="ts">
// Редактирование статьи
// Props: articleId: number
// Store: useArticleStore → fetchArticleById (предзаполнение), updateArticle()
// После успеха → router.push({ name: 'article', params: { id: articleId } })
defineProps<{ articleId: number }>()
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Редактировать статью</h1>
    <!-- TODO: форма с предзаполненными данными -->
  </div>
</template>
