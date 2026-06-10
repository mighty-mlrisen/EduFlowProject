import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import type { ArticleResponse } from '@/types/article.types'

export type SortKey = 'date-desc' | 'date-asc' | 'likes' | 'comments'

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'date-desc', label: 'Новые' },
  { value: 'date-asc', label: 'Старые' },
  { value: 'likes', label: 'По лайкам' },
  { value: 'comments', label: 'По комментариям' },
]

export function useArticleSort(articles: Ref<ArticleResponse[]>) {
  const sortKey = ref<SortKey>('date-desc')

  const sorted = computed(() => {
    const arr = [...articles.value]
    switch (sortKey.value) {
      case 'date-asc':
        return arr.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
      case 'likes':
        return arr.sort((a, b) => (b.likes ?? 0) - (a.likes ?? 0))
      case 'comments':
        return arr.sort((a, b) => (b.commentsCount ?? 0) - (a.commentsCount ?? 0))
      default:
        return arr.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    }
  })

  return { sortKey, sorted }
}
