import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { getColumn } from '../constants'
import { daysSince, formatDate, relativeDaysLabel } from '../lib/dates'
import { GripIcon, LinkedInIcon, PencilIcon, TrashIcon } from './Icons'

function ageTone(job) {
  if (job.status === 'wishlist') return 'text-slate-500 dark:text-slate-400'
  const days = daysSince(job.dateApplied)
  if (days !== null && days >= 30) return 'text-rose-600 dark:text-rose-400'
  if (days !== null && days >= 14) return 'text-amber-700 dark:text-amber-400'
  return 'text-slate-500 dark:text-slate-400'
}

function stopInteraction(event) {
  event.stopPropagation()
}

export function JobCardView({ job, overlay = false, showGrip = false, onEdit, onDelete }) {
  const column = getColumn(job.status)

  return (
    <article
      className={`rounded-lg border border-y-slate-200 border-r-slate-200 border-l-4 bg-white p-3 shadow-sm transition dark:border-y-slate-800 dark:border-r-slate-800 dark:bg-slate-900 ${
        column.accent
      } ${overlay ? 'rotate-1 shadow-lg' : 'hover:shadow-md'}`}
    >
      <div className="flex items-start justify-between gap-2">
        {showGrip && (
          <span
            aria-hidden="true"
            title="Drag to move between columns"
            className="-ml-1 shrink-0 text-slate-400 opacity-0 transition group-hover:opacity-100 dark:text-slate-500"
          >
            <GripIcon />
          </span>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
            {job.company}
          </h3>
          <p className="mt-0.5 truncate text-xs text-slate-600 dark:text-slate-400">{job.title}</p>
        </div>
        {!overlay && (
          <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
            <button
              type="button"
              title="Edit job"
              aria-label={`Edit ${job.company}`}
              onClick={(event) => {
                event.stopPropagation()
                onEdit(job)
              }}
              onPointerDown={stopInteraction}
              className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            >
              <PencilIcon />
            </button>
            <button
              type="button"
              title="Delete job"
              aria-label={`Delete ${job.company}`}
              onClick={(event) => {
                event.stopPropagation()
                onDelete(job)
              }}
              onPointerDown={stopInteraction}
              className="rounded p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950 dark:hover:text-rose-400"
            >
              <TrashIcon />
            </button>
          </div>
        )}
      </div>

      {(job.resume || job.salary) && (
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {job.resume && (
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {job.resume}
            </span>
          )}
          {job.salary && (
            <span className="rounded border border-slate-200 px-1.5 py-0.5 text-[11px] text-slate-600 dark:border-slate-700 dark:text-slate-300">
              {job.salary}
            </span>
          )}
        </div>
      )}

      {job.notes && (
        <p className="mt-2 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{job.notes}</p>
      )}

      <div className="mt-2.5 flex items-center justify-between gap-2 border-t border-slate-100 pt-2 dark:border-slate-800">
        <span
          className={`inline-flex items-center gap-1 text-[11px] font-medium ${ageTone(job)}`}
          title={`${column.dateLabel}: ${formatDate(job.dateApplied)}`}
        >
          {relativeDaysLabel(job.dateApplied, column.dateLabel)}
        </span>
        {job.url ? (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open job posting on LinkedIn"
            aria-label={`Open ${job.company} job posting on LinkedIn`}
            onClick={stopInteraction}
            onPointerDown={stopInteraction}
            className="rounded p-1 text-[#0A66C2] hover:bg-slate-100 dark:text-[#70b5f9] dark:hover:bg-slate-800"
          >
            <LinkedInIcon />
          </a>
        ) : (
          <span className="text-[11px] text-slate-500 dark:text-slate-400">No link</span>
        )}
      </div>
    </article>
  )
}

export default function JobCard({ job, disabled = false, onEdit, onDelete, onClick }) {
  const { listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: job.id,
    disabled,
    data: { type: 'card', status: job.status },
  })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      onClick={onClick}
      className={`group touch-none ${isDragging ? 'opacity-40' : ''} ${disabled ? '' : 'cursor-grab active:cursor-grabbing'}`}
      {...listeners}
    >
      <JobCardView job={job} showGrip={!disabled} onEdit={onEdit} onDelete={onDelete} />
    </div>
  )
}
