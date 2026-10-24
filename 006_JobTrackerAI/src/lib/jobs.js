import { STATUS_IDS, STATUS_LABELS } from '../constants'
import { toISODate } from './dates'

function sortKey(job) {
  return (job.dateApplied || job.createdAt || '').slice(0, 10)
}

export function byOrder(a, b) {
  return (a.order ?? 0) - (b.order ?? 0)
}

export function newId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `job-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function normalizeUrl(value) {
  const url = (value ?? '').trim()
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return `https://${url}`
}

export function isUrlLike(value) {
  const raw = (value ?? '').trim()
  // Browsers happily percent-encode spaces, so "not a url" would otherwise
  // pass as https://not%20a%20url/. Require a real dotted host instead.
  if (!raw || /\s/.test(raw)) return false
  try {
    const url = new URL(normalizeUrl(raw))
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return false
    return url.hostname.includes('.')
  } catch {
    return false
  }
}

export function normalizeJob(raw) {
  const now = new Date().toISOString()
  const status = STATUS_IDS.includes(raw?.status) ? raw.status : STATUS_IDS[0]
  return {
    id: raw?.id || newId(),
    company: (raw?.company ?? '').toString().trim(),
    title: (raw?.title ?? '').toString().trim(),
    url: raw?.url ? normalizeUrl(raw.url) : '',
    resume: (raw?.resume ?? '').toString().trim(),
    dateApplied: raw?.dateApplied ? toISODate(raw.dateApplied) : toISODate(now),
    salary: (raw?.salary ?? '').toString().trim(),
    notes: (raw?.notes ?? '').toString().trim(),
    status,
    order: Number.isFinite(raw?.order) ? raw.order : 0,
    createdAt: raw?.createdAt || now,
    updatedAt: raw?.updatedAt || now,
  }
}

export function groupByStatus(jobs) {
  const groups = Object.fromEntries(STATUS_IDS.map((status) => [status, []]))
  for (const job of jobs) {
    const bucket = groups[job.status] ?? groups[STATUS_IDS[0]]
    bucket.push(job)
  }
  for (const status of STATUS_IDS) {
    groups[status].sort(byOrder)
  }
  return groups
}

export function nextOrder(jobs, status) {
  const orders = jobs.filter((job) => job.status === status).map((job) => job.order ?? 0)
  return orders.length ? Math.max(...orders) + 1 : 0
}

export function orderInColumn(jobs, status) {
  const orderById = new Map(
    jobs
      .filter((job) => job.status === status)
      .sort(byOrder)
      .map((job, index) => [job.id, index]),
  )
  return jobs.map((job) =>
    orderById.has(job.id) && job.order !== orderById.get(job.id)
      ? { ...job, order: orderById.get(job.id) }
      : job,
  )
}

export function moveJob(jobs, activeId, toStatus, toIndex) {
  const active = jobs.find((job) => job.id === activeId)
  if (!active) return jobs
  const destination = jobs
    .filter((job) => job.status === toStatus && job.id !== activeId)
    .sort(byOrder)
  const index = Math.max(0, Math.min(toIndex ?? destination.length, destination.length))
  destination.splice(index, 0, { ...active, status: toStatus })

  const orderById = new Map(destination.map((job, position) => [job.id, position]))
  let next = jobs.map((job) =>
    job.id === activeId ? { ...job, status: toStatus } : job,
  )
  next = next.map((job) =>
    orderById.has(job.id) ? { ...job, order: orderById.get(job.id) } : job,
  )
  if (active.status !== toStatus) return orderInColumn(next, active.status)
  return next
}

export function sortColumnByDate(jobs, status, direction) {
  const sorted = jobs
    .filter((job) => job.status === status)
    .sort((a, b) => {
      const diff = sortKey(a).localeCompare(sortKey(b))
      return diff === 0 ? byOrder(a, b) : direction === 'asc' ? diff : -diff
    })
  const orderById = new Map(sorted.map((job, index) => [job.id, index]))
  return jobs.map((job) =>
    orderById.has(job.id) && job.order !== orderById.get(job.id)
      ? { ...job, order: orderById.get(job.id) }
      : job,
  )
}

export function changedJobs(next, previous) {
  const previousById = new Map(previous.map((job) => [job.id, job]))
  return next.filter((job) => {
    const before = previousById.get(job.id)
    if (!before) return true
    return (
      before.status !== job.status ||
      before.order !== job.order ||
      before.updatedAt !== job.updatedAt
    )
  })
}

export function resumeOptions(jobs, defaults) {
  const names = new Set(defaults)
  for (const job of jobs) {
    if (job.resume) names.add(job.resume)
  }
  return [...names].sort((a, b) => a.localeCompare(b))
}

export function describeStatusCounts(jobs) {
  const groups = groupByStatus(jobs)
  return STATUS_IDS.map((status) => ({
    status,
    label: STATUS_LABELS[status],
    count: groups[status].length,
  }))
}
