import { DownloadIcon, MoonIcon, PlusIcon, SearchIcon, SunIcon, UploadIcon } from './Icons'

const buttonClass =
  'inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100'

export default function Toolbar({
  query,
  onQueryChange,
  onAddJob,
  onExport,
  onImport,
  theme,
  onToggleTheme,
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative">
        <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search company or role"
          aria-label="Search jobs by company or role"
          className="w-56 rounded-lg border border-slate-300 bg-white py-2 pr-3 pl-8 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500"
        />
      </div>

      <button
        type="button"
        onClick={onAddJob}
        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-500/40 focus:outline-none"
      >
        <PlusIcon />
        Add job
      </button>

      <button type="button" onClick={onExport} title="Download all jobs as JSON" className={buttonClass}>
        <DownloadIcon />
        Export
      </button>

      <button type="button" onClick={onImport} title="Restore jobs from a JSON backup" className={buttonClass}>
        <UploadIcon />
        Import
      </button>

      <button
        type="button"
        onClick={onToggleTheme}
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        className={buttonClass}
      >
        {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
      </button>
    </div>
  )
}
