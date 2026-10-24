import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { DEFAULT_RESUMES, STATUS_IDS } from '../constants'
import { deleteJob as dbDeleteJob, getAllJobs, putJobs, replaceAllJobs } from '../db'
import {
  changedJobs,
  groupByStatus,
  moveJob,
  newId,
  nextOrder,
  normalizeJob,
  orderInColumn,
  resumeOptions,
  sortColumnByDate,
} from '../lib/jobs'

export function useJobs() {
  const [jobs, setJobs] = useState([])
  const [phase, setPhase] = useState('loading')
  const [error, setError] = useState(null)
  const jobsRef = useRef([])
  const baselineRef = useRef(null)

  const apply = useCallback((next) => {
    jobsRef.current = next
    setJobs(next)
    return next
  }, [])

  const persist = useCallback((changed) => {
    if (!changed.length) return
    putJobs(changed).catch((err) => {
      console.error('Could not save to IndexedDB', err)
      setError(err instanceof Error ? err : new Error(String(err)))
    })
  }, [])

  const commit = useCallback(
    (next) => {
      const changed = changedJobs(next, jobsRef.current)
      apply(next)
      persist(changed)
    },
    [apply, persist],
  )

  useEffect(() => {
    let cancelled = false
    getAllJobs()
      .then((records) => {
        if (cancelled) return
        apply(records.map(normalizeJob))
        setPhase('ready')
      })
      .catch((err) => {
        if (cancelled) return
        console.error('Could not read from IndexedDB', err)
        setError(err instanceof Error ? err : new Error(String(err)))
        setPhase('error')
      })
    return () => {
      cancelled = true
    }
  }, [apply])

  const addJob = useCallback(
    (values) => {
      const current = jobsRef.current
      const status = STATUS_IDS.includes(values.status) ? values.status : STATUS_IDS[0]
      const job = normalizeJob({
        ...values,
        id: newId(),
        status,
        order: nextOrder(current, status),
      })
      commit([...current, job])
      return job
    },
    [commit],
  )

  const updateJob = useCallback(
    (id, values) => {
      const current = jobsRef.current
      const existing = current.find((job) => job.id === id)
      if (!existing) return null
      const status = STATUS_IDS.includes(values.status) ? values.status : existing.status
      let next = current
      if (status !== existing.status) {
        next = moveJob(current, id, status, Number.MAX_SAFE_INTEGER)
      }
      const placed = next.find((job) => job.id === id) ?? existing
      const updated = normalizeJob({
        ...placed,
        ...values,
        id,
        status,
        order: placed.order,
        createdAt: existing.createdAt,
        updatedAt: new Date().toISOString(),
      })
      commit(next.map((job) => (job.id === id ? updated : job)))
      return updated
    },
    [commit],
  )

  const removeJob = useCallback(
    (id) => {
      const current = jobsRef.current
      const removed = current.find((job) => job.id === id)
      if (!removed) return
      commit(orderInColumn(current.filter((job) => job.id !== id), removed.status))
      dbDeleteJob(id).catch((err) => {
        console.error('Could not delete from IndexedDB', err)
        setError(err instanceof Error ? err : new Error(String(err)))
      })
    },
    [commit],
  )

  const beginDrag = useCallback(() => {
    baselineRef.current = jobsRef.current
  }, [])

  const moveLocal = useCallback(
    (activeId, toStatus, toIndex) => {
      apply(moveJob(jobsRef.current, activeId, toStatus, toIndex))
    },
    [apply],
  )

  const endDrag = useCallback(
    () => {
      const baseline = baselineRef.current
      baselineRef.current = null
      if (!baseline) return
      persist(changedJobs(jobsRef.current, baseline))
    },
    [persist],
  )

  const sortColumn = useCallback(
    (status, direction) => {
      commit(sortColumnByDate(jobsRef.current, status, direction))
    },
    [commit],
  )

  const importJobs = useCallback(
    async (records, { replace = false } = {}) => {
      const incoming = records.map(normalizeJob)
      let next = []
      if (replace) {
        const seen = new Set()
        for (const job of incoming) {
          if (seen.has(job.id)) continue
          seen.add(job.id)
          next.push(job)
        }
        for (const status of STATUS_IDS) next = orderInColumn(next, status)
        apply(next)
        try {
          await replaceAllJobs(next)
        } catch (err) {
          console.error('Could not restore jobs into IndexedDB', err)
          setError(err instanceof Error ? err : new Error(String(err)))
          throw err
        }
        return next.length
      }
      const byId = new Map(jobsRef.current.map((job) => [job.id, job]))
      for (const job of incoming) byId.set(job.id, job)
      next = [...byId.values()]
      for (const status of STATUS_IDS) next = orderInColumn(next, status)
      commit(next)
      return incoming.length
    },
    [apply, commit],
  )

  const exportData = useCallback(() => {
    const ordered = []
    for (const status of STATUS_IDS) {
      ordered.push(...jobsRef.current.filter((job) => job.status === status).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))
    }
    return {
      app: 'job-tracker',
      version: 1,
      exportedAt: new Date().toISOString(),
      count: ordered.length,
      jobs: ordered,
    }
  }, [])

  const groups = useMemo(() => groupByStatus(jobs), [jobs])

  const resumes = useMemo(() => resumeOptions(jobs, DEFAULT_RESUMES), [jobs])

  return {
    jobs,
    groups,
    resumes,
    phase,
    error,
    addJob,
    updateJob,
    removeJob,
    beginDrag,
    moveLocal,
    endDrag,
    sortColumn,
    importJobs,
    exportData,
  }
}
