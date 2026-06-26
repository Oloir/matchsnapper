import { api } from './client'

export interface SnapshotItemOut {
  tag_id: string
  tag_name: string
  weight: string
}

export interface SnapshotOut {
  items: SnapshotItemOut[]
}

export const snapshotsApi = {
  get: () => api.get<SnapshotOut>('/snapshots/me').then(r => r.data),

  replace: (items: { tag_id: string; weight: string }[]) =>
    api.put<SnapshotOut>('/snapshots/me', items).then(r => r.data),

  upsertItem: (tag_id: string, weight: string) =>
    api.patch<SnapshotOut>('/snapshots/me/items', { tag_id, weight }).then(r => r.data),

  deleteItem: (tag_id: string) =>
    api.delete(`/snapshots/me/items/${tag_id}`),
}
