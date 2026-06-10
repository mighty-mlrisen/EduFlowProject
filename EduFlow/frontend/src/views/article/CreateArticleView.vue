<script setup lang="ts">
// Создание новой статьи
// Store: useArticleStore → createArticle(), fetchCategories(), categories
// После успеха → router.push({ name: 'article', params: { id: created.articleId } })
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Новая статья</h1>
    <!-- TODO: форма categoryName/title/description/text/image/draft -->
  </div>
</template>
