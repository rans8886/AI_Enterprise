export const COLUMNS = [
  {
    id: 'wishlist',
    label: 'Wishlist',
    hint: 'Saved, not applied yet',
    dateLabel: 'Saved',
    dot: 'bg-slate-400',
    accent: 'border-l-slate-400',
    tint: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  },
  {
    id: 'applied',
    label: 'Applied',
    hint: 'Application submitted',
    dateLabel: 'Applied',
    dot: 'bg-blue-500',
    accent: 'border-l-blue-500',
    tint: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  },
  {
    id: 'followup',
    label: 'Follow-up',
    hint: 'Chased recruiter or referral',
    dateLabel: 'Applied',
    dot: 'bg-amber-500',
    accent: 'border-l-amber-500',
    tint: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  },
  {
    id: 'interview',
    label: 'Interview',
    hint: 'In interview rounds',
    dateLabel: 'Applied',
    dot: 'bg-violet-500',
    accent: 'border-l-violet-500',
    tint: 'bg-violet-50 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
  },
  {
    id: 'offer',
    label: 'Offer',
    hint: 'Offer received',
    dateLabel: 'Applied',
    dot: 'bg-emerald-500',
    accent: 'border-l-emerald-500',
    tint: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  },
  {
    id: 'rejected',
    label: 'Rejected',
    hint: 'Not moving forward',
    dateLabel: 'Applied',
    dot: 'bg-rose-500',
    accent: 'border-l-rose-500',
    tint: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  },
]

export const STATUS_IDS = COLUMNS.map((column) => column.id)

export const STATUS_LABELS = Object.fromEntries(COLUMNS.map((column) => [column.id, column.label]))

export const DEFAULT_RESUMES = ['SDE_Resume_v3', 'QA_Lead_Resume']

export function getColumn(status) {
  return COLUMNS.find((column) => column.id === status) ?? COLUMNS[0]
}
