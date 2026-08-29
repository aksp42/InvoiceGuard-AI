const API_BASE = '/api'

async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

function uploadRequest(file, mode, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/upload/${mode}`)
    const token = localStorage.getItem('token')
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      let data = {}
      try { data = JSON.parse(xhr.responseText || '{}') } catch { data = {} }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data)
      else reject(new Error(data.detail || `Upload failed (${xhr.status})`))
    }
    xhr.onerror = () => reject(new Error('Network error — could not reach the upload API'))
    xhr.send(form)
  })
}

export const api = {
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  uploadSingle: (file, onProgress) => uploadRequest(file, 'single', onProgress),
  uploadBulk:   (file, onProgress) => uploadRequest(file, 'bulk',   onProgress),
  uploadHistory: ()       => request('/upload/history'),
  uploadBatch:   (id)     => request(`/upload/${encodeURIComponent(id)}`),

  validateBatch: (id) => request(`/validate/${encodeURIComponent(id)}`, { method: 'POST' }),

  scanDuplicates: (id) => request(`/duplicates/${encodeURIComponent(id)}`, { method: 'POST' }),
  listDuplicates: () => request('/duplicates'),

  listInvoices: ()     => request('/invoices'),
  getInvoice:   (id)   => request(`/invoices/${encodeURIComponent(id)}`),
  health:       ()     => request('/health'),
}

export const apiUrl = API_BASE