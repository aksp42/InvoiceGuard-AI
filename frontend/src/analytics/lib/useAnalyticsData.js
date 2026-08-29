// Phase 6 — Shared data hook: loads invoices, upload history and duplicate
// pairs in parallel from the existing REST API, with error handling + retry.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../services/api.js'

export default function useAnalyticsData() {
  const [state, setState] = useState({
    invoices: null,
    batches: null,
    pairs: null,
    loading: true,
    error: '',
  })

  const load = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: '' }))
    Promise.allSettled([
      api.listInvoices(),
      api.uploadHistory(),
      api.listDuplicates(),
    ]).then(([inv, bat, dup]) => {
      const errors = []
      if (inv.status === 'rejected') errors.push('invoices: ' + inv.reason?.message)
      if (bat.status === 'rejected') errors.push('uploads: ' + bat.reason?.message)
      // duplicates may be empty/unsupported → not fatal
      setState({
        invoices: inv.status === 'fulfilled' ? inv.value : [],
        batches: bat.status === 'fulfilled' ? bat.value : [],
        pairs: dup.status === 'fulfilled' ? dup.value : [],
        loading: false,
        error: errors.join(' · '),
      })
    })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { ...state, reload: load }
}
