const MS_PER_DAY = 24 * 60 * 60 * 1000

export function toISODate(date) {
  if (typeof date === 'string') {
    // Date-only strings must not round-trip through Date: parsing "2026-03-12"
    // is UTC midnight, which shifts to the previous day in negative offsets.
    const match = /^(\d{4}-\d{2}-\d{2})/.exec(date.trim())
    if (match) return match[1]
  }
  const parsed = date instanceof Date ? date : new Date(date)
  if (Number.isNaN(parsed.getTime())) return ''
  const month = String(parsed.getMonth() + 1).padStart(2, '0')
  const day = String(parsed.getDate()).padStart(2, '0')
  return `${parsed.getFullYear()}-${month}-${day}`
}

export function todayISO() {
  return toISODate(new Date())
}

export function parseISODate(value) {
  if (!value) return null
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return null
  const date = new Date(year, month - 1, day)
  return Number.isNaN(date.getTime()) ? null : date
}

export function daysSince(value) {
  const date = parseISODate(value)
  if (!date) return null
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.round((today.getTime() - date.getTime()) / MS_PER_DAY)
}

export function formatDate(value) {
  const date = parseISODate(value)
  if (!date) return 'Not set'
  return date.toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function relativeDaysLabel(value, prefix = '') {
  const days = daysSince(value)
  const lead = prefix ? `${prefix} ` : ''
  if (days === null) return 'No date set'
  if (days === 0) return `${lead}today`
  if (days === 1) return `${lead}1 day ago`
  if (days < 0) return `${lead}in ${Math.abs(days)} days`
  return `${lead}${days} days ago`
}
