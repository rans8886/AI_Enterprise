import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import JobCard from './JobCard'
import { PlusIcon, SortDownIcon, SortUpIcon } from './Icons'

export default function Column({
  column,
  jobs,
  sortDirection,
  dragDisabled,
  onSortToggle,
  onAdd,
  onEdit,
  onDelete,
  onCardClick,
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
    data: { type: 'column', status: column.id },
  })

  const sortLabel = sortDirection === 'desc' ? 'Newest first' : 'Oldest first'

  return (
    <section className="flex h-full w-[18rem] min-w-[18rem] flex-col rounded-xl border border-slate-200 bg-slate-100/60 dark:border-slate-800 dark:bg-slate-900/40">
      <header className="flex items-center justify-between gap-2 px-3 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <span className={`size-2 shrink-0 rounded-full ${column.dot}`} />
          <h2 className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
            {column.label}
          </h2>
          <span
            className={`rounded-full px-1.5 py-0.5 text-[11px] font-semibold ${column.tint}`}
          >
            {jobs.length}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-0.5 text-slate-400">
          <button
            type="button"
            onClick={onSortToggle}
            title={`Sort by date — currently ${sortLabel.toLowerCase()}`}
            aria-label={`Sort ${column.label} by date, currently ${sortLabel}`}
            className="rounded p-1 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            {sortDirection === 'desc' ? <SortDownIcon /> : <SortUpIcon />}
          </button>
          <button
            type="button"
            onClick={() => onAdd(column.id)}
            title={`Add job to ${column.label}`}
            aria-label={`Add job to ${column.label}`}
            className="rounded p-1 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            <PlusIcon />
          </button>
        </div>
      </header>

      <div
        ref={setNodeRef}
        className={`scroll-thin flex-1 space-y-2 overflow-y-auto rounded-b-xl px-2.5 pb-3 transition-colors ${
          isOver ? 'bg-indigo-50/70 dark:bg-indigo-950/30' : ''
        }`}
      >
        <SortableContext items={jobs.map((job) => job.id)} strategy={verticalListSortingStrategy}>
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              disabled={dragDisabled}
              onEdit={onEdit}
              onDelete={onDelete}
              onClick={() => onCardClick(job)}
            />
          ))}
        </SortableContext>

        {jobs.length === 0 && (
          <div className="flex h-24 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 px-3 text-center dark:border-slate-700">
            <p className="text-xs text-slate-600 dark:text-slate-400">{column.hint}</p>
            <button
              type="button"
              onClick={() => onAdd(column.id)}
              className="mt-1 text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              Add a job
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
