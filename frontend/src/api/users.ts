import { api } from './client'

export interface UserMe {
  id: string
  email: string
  username: string
  avatar_url: string | null
  bio: string | null
  is_active: boolean
  created_at: string
}

export const usersApi = {
  getMe: () => api.get<UserMe>('/users/me').then(r => r.data),

  patchMe: (bio: string | null) =>
    api.patch<UserMe>('/users/me', { bio }).then(r => r.data),

  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('avatar', file)
    return api.post<{ avatar_url: string }>('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  deleteAvatar: () => api.delete('/users/me/avatar'),

  markViewed: (userId: string) =>
    api.post(`/users/${userId}/view`).then(r => r.data),

  unmarkViewed: (userId: string) => api.delete(`/users/${userId}/view`),

  sendContact: (userId: string) =>
    api.post(`/users/${userId}/contact`).then(r => r.data),

  getPublic: (userId: string) =>
    api.get<UserMe>(`/users/${userId}`).then(r => r.data),

  getPublicSnapshot: (userId: string) =>
    api.get<{ items: { tag_id: string; tag_name: string; weight: string }[] }>(`/users/${userId}/snapshot`).then(r => r.data),
}
