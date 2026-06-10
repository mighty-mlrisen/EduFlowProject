export interface ApiError {
  statusCode: number
  message: string
  description: string
  errors: string[] | null
}

export interface PaginationMeta {
  page: number
  size: number
  total: number
}
