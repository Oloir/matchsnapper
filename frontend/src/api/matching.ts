import { api } from './client'

export interface CommonTag {
  tag: string
  weight_mine: string
  weight_theirs: string
}

export interface MatchUser {
  id: string
  username: string
  avatar_url: string | null
  bio: string | null
}

export interface MatchResult {
  user: MatchUser
  score: number
  is_viewed: boolean
  common_tags: CommonTag[]
}

export interface MatchList {
  results: MatchResult[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface Tag {
  id: string
  name: string
  category: string | null
}

export interface TagList {
  items: Tag[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface SimilarityResponse {
  user_id: string
  score: number
  common_tags: CommonTag[]
}

export const matchingApi = {
  list: (page = 1, limit = 20) =>
    api.get<MatchList>('/matching', { params: { page, limit } }).then(r => r.data),

  getSimilarity: (userId: string) =>
    api.get<SimilarityResponse>(`/matching/${userId}`).then(r => r.data),
}

export const tagsApi = {
  search: (q: string, page = 1, limit = 10) =>
    api.get<TagList>('/tags', { params: { q, page, limit } }).then(r => r.data),

  create: (name: string) =>
    api.post<Tag>('/tags', { name }).then(r => r.data),
}
