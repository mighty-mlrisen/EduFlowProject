export interface ArticleStatEntry {
  articleId: number
  title: string
  authorUsername: string | null
  authorAvatar: string | null
  count: number
}

export interface AuthorStatEntry {
  userId: number
  username: string
  login: string
  avatar: string | null
  count: number
}

export interface CategoryStatEntry {
  categoryName: string
  articleCount: number
}

export interface GlobalStatsResponse {
  totalUsers: number
  totalArticles: number
  totalPublished: number
  totalDrafts: number
  totalComments: number
  totalLikes: number
  totalSubscriptions: number
  newUsersLastWeek: number
  top10ArticlesByLikes: ArticleStatEntry[]
  top10AuthorsByLikes: AuthorStatEntry[]
  top10AuthorsBySubscribers: AuthorStatEntry[]
  categoryStats: CategoryStatEntry[]
}

export interface UserStatsResponse {
  publishedArticles: number
  drafts: number
  commentsGiven: number
  savedArticlesCount: number
  totalLikesReceived: number
  avgLikesPerArticle: number
  followersCount: number
  subscriptionsCount: number
  articlesLast30Days: number
  commentsLast30Days: number
  lastPublicationDate: string | null
  top5ArticlesByLikes: ArticleStatEntry[]
  top5ArticlesByComments: ArticleStatEntry[]
}
