import { useEffect, useMemo, useRef, useState } from 'react'
import Board from './components/Board'
import ConfirmDialog from './components/ConfirmDialog'
import { BriefcaseIcon } from './components/Icons'
import JobForm from './components/JobForm'
import Toolbar from './components/Toolbar'
import { STATUS_IDS } from './constants'
import { useJobs } from './hooks/useJobs'
import { useTheme } from './hooks/useTheme'
import { todayISO } from './lib/dates'

export default function App() {
  const {
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
  } = useJobs()
  const { theme, toggleTheme } = useTheme()

  const [query, setQuery] = useState('')
  const [form, setForm] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [notice, setNotice] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (!notice) return undefined
    const timer = setTimeout(() => setNotice(null), 5000)
    return () => clearTimeout(timer)
  }, [notice])

  const search = query.trim().toLowerCase()
  const filtering = search.length > 0

  const visibleGroups = useMemo(() => {
    if (!filtering) return groups
    const matches = (job) =>
      job.company.toLowerCase().includes(search) || job.title.toLowerCase().includes(search)
    return Object.fromEntries(
      STATUS_IDS.map((status) => [status, (groups[status] ?? []).filter(matches)]),
    )
  }, [groups, filtering, search])

  const visibleCount = useMemo(
    () => STATUS_IDS.reduce((total, status) => total + (visibleGroups[status]?.length ?? 0), 0),
    [visibleGroups],
  )

  function handleSubmit(values) {
    if (form?.job) {
      updateJob(form.job.id, values)
      setNotice({ tone: 'success', text: `Updated ${values.company}.` })
    } else {
      addJob(values)
      setNotice({ tone: 'success', text: `Added ${values.company} to ${values.status}.` })
    }
    setForm(null)
  }

  function handleConfirmDelete() {
    if (!pendingDelete) return
    removeJob(pendingDelete.id)
    setNotice({ tone: 'success', text: `Deleted ${pendingDelete.company}.` })
    setPendingDelete(null)
  }

  function handleExport() {
    const payload = exportData()
    if (!payload.count) {
      setNotice({ tone: 'error', text: 'There is nothing to export yet.' })
      return
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `job-tracker-backup-${todayISO()}.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    // Revoking straight away can abort the download before Chrome starts it.
    setTimeout(() => URL.revokeObjectURL(url), 10000)
    setNotice({ tone: 'success', text: `Exported ${payload.count} job(s) as JSON.` })
  }

  async function handleImportFile(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    try {
      const parsed = JSON.parse(await file.text())
      const records = Array.isArray(parsed) ? parsed : parsed?.jobs
      if (!Array.isArray(records)) {
        throw new Error('that file is not a Job Tracker backup')
      }
      const valid = records.filter((record) => record && (record.company || record.title))
      if (!valid.length) throw new Error('no job records were found in that file')
      const total = await importJobs(valid, { replace: false })
      setNotice({
        tone: 'success',
        text: `Imported ${valid.length} job(s). Your board now holds ${total}.`,
      })
    } catch (err) {
      setNotice({ tone: 'error', text: `Import failed: ${err.message}` })
    }
  }

  return (
    <div className="flex h-full flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="shrink-0 border-b border-slate-200 bg-white/80 px-5 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/60">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
              <BriefcaseIcon className="size-5" />
            </span>
            <div>
              <h1 className="text-base leading-tight font-semibold">Job Tracker</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {jobs.length} job{jobs.length === 1 ? '' : 's'} tracked · saved in this browser only
              </p>
            </div>
          </div>
          <Toolbar
            query={query}
            onQueryChange={setQuery}
            onAddJob={() => setForm({ job: null, status: STATUS_IDS[0] })}
            onExport={handleExport}
            onImport={() => fileInputRef.current?.click()}
            theme={theme}
            onToggleTheme={toggleTheme}
          />
        </div>
      </header>

      {error && (
        <p className="border-b border-rose-200 bg-rose-50 px-5 py-2 text-xs text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300">
          Local storage problem: {error.message}. Changes may not be saved.
        </p>
      )}

      {notice && (
        <p
          className={`border-b px-5 py-2 text-xs ${
            notice.tone === 'error'
              ? 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300'
              : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300'
          }`}
        >
          {notice.text}
        </p>
      )}

      {filtering && (
        <p className="border-b border-slate-200 bg-white/60 px-5 py-1.5 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-400">
          Showing {visibleCount} of {jobs.length} match{visibleCount === 1 ? '' : 'es'} · clear the
          search to drag cards
        </p>
      )}

      <main className="flex min-h-0 flex-1 flex-col p-4">
        {phase === 'loading' ? (
          <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
            Opening your local database…
          </div>
        ) : (
          <Board
            groups={visibleGroups}
            dragDisabled={filtering}
            onBeginDrag={beginDrag}
            onMoveLocal={moveLocal}
            onEndDrag={endDrag}
            onSortColumn={sortColumn}
            onAdd={(status) => setForm({ job: null, status })}
            onEdit={(job) => setForm({ job, status: job.status })}
            onDelete={setPendingDelete}
          />
        )}
      </main>

      {form && (
        <JobForm
          key={form.job?.id ?? `new-${form.status}`}
          job={form.job}
          defaultStatus={form.status}
          resumes={resumes}
          onClose={() => setForm(null)}
          onSubmit={handleSubmit}
        />
      )}

      {pendingDelete && (
        <ConfirmDialog
          title={`Delete ${pendingDelete.company}?`}
          message={`"${pendingDelete.title}" will be permanently removed from your board. This cannot be undone.`}
          confirmLabel="Delete job"
          onConfirm={handleConfirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={handleImportFile}
      />
    </div>
  )
}
