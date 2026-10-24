import { useEffect, useRef, useState } from 'react'
import { COLUMNS, STATUS_IDS } from '../constants'
import { todayISO } from '../lib/dates'
import { isUrlLike, normalizeUrl } from '../lib/jobs'
import { CloseIcon } from './Icons'

const fieldClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500'

const labelClass = 'mb-1 block text-xs font-medium text-slate-600 dark:text-slate-300'

const errorClass = 'mt-1 text-xs font-medium text-rose-600 dark:text-rose-400'

function validate(values) {
  const errors = {}
  if (!values.company.trim()) errors.company = 'Company name is required.'
  if (!values.title.trim()) errors.title = 'Job title is required.'
  if (values.url.trim() && !isUrlLike(values.url)) {
    errors.url = 'Enter a valid link, e.g. https://www.linkedin.com/jobs/view/123'
  }
  if (!values.dateApplied) errors.dateApplied = 'Pick the date applied.'
  return errors
}

export default function JobForm({ job, defaultStatus, resumes, onClose, onSubmit }) {
  const isEdit = Boolean(job)
  const [values, setValues] = useState(() => ({
    company: job?.company ?? '',
    title: job?.title ?? '',
    url: job?.url ?? '',
    resume: job?.resume ?? '',
    dateApplied: job?.dateApplied ?? todayISO(),
    salary: job?.salary ?? '',
    notes: job?.notes ?? '',
    status: job?.status ?? defaultStatus ?? STATUS_IDS[0],
  }))
  const [errors, setErrors] = useState({})
  const companyRef = useRef(null)

  useEffect(() => {
    companyRef.current?.focus()
  }, [])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  function update(field) {
    return (event) => {
      const { value } = event.target
      setValues((prev) => ({ ...prev, [field]: value }))
      setErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev))
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    const nextErrors = validate(values)
    const hasErrors = Object.values(nextErrors).some(Boolean)
    setErrors(nextErrors)
    if (hasErrors) return
    onSubmit({
      company: values.company.trim(),
      title: values.title.trim(),
      url: values.url.trim() ? normalizeUrl(values.url) : '',
      resume: values.resume.trim(),
      dateApplied: values.dateApplied,
      salary: values.salary.trim(),
      notes: values.notes.trim(),
      status: values.status,
    })
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div
        className="fade-in absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />
      <form
        onSubmit={handleSubmit}
        role="dialog"
        aria-modal="true"
        aria-labelledby="job-form-title"
        className="slide-in-right relative flex h-full w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900"
      >
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div>
            <h2
              id="job-form-title"
              className="text-base font-semibold text-slate-900 dark:text-slate-100"
            >
              {isEdit ? 'Edit job' : 'Add a job'}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {isEdit ? 'Changes save to this browser instantly.' : 'Saved locally in IndexedDB.'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            <CloseIcon className="size-4" />
          </button>
        </header>

        <div className="scroll-thin flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <div>
            <label className={labelClass} htmlFor="company">
              Company name <span className="text-rose-500">*</span>
            </label>
            <input
              id="company"
              ref={companyRef}
              value={values.company}
              onChange={update('company')}
              placeholder="Acme Corp"
              aria-invalid={Boolean(errors.company)}
              className={fieldClass}
            />
            {errors.company && <p className={errorClass}>{errors.company}</p>}
          </div>

          <div>
            <label className={labelClass} htmlFor="title">
              Job title <span className="text-rose-500">*</span>
            </label>
            <input
              id="title"
              value={values.title}
              onChange={update('title')}
              placeholder="Senior Frontend Engineer"
              aria-invalid={Boolean(errors.title)}
              className={fieldClass}
            />
            {errors.title && <p className={errorClass}>{errors.title}</p>}
          </div>

          <div>
            <label className={labelClass} htmlFor="url">
              LinkedIn job URL
            </label>
            <input
              id="url"
              value={values.url}
              onChange={update('url')}
              placeholder="https://www.linkedin.com/jobs/view/..."
              aria-invalid={Boolean(errors.url)}
              className={fieldClass}
            />
            {errors.url && <p className={errorClass}>{errors.url}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass} htmlFor="status">
                Status
              </label>
              <select id="status" value={values.status} onChange={update('status')} className={fieldClass}>
                {COLUMNS.map((column) => (
                  <option key={column.id} value={column.id}>
                    {column.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass} htmlFor="dateApplied">
                Date applied <span className="text-rose-500">*</span>
              </label>
              <input
                id="dateApplied"
                type="date"
                value={values.dateApplied}
                onChange={update('dateApplied')}
                aria-invalid={Boolean(errors.dateApplied)}
                className={fieldClass}
              />
              {errors.dateApplied && <p className={errorClass}>{errors.dateApplied}</p>}
            </div>
          </div>

          <div>
            <label className={labelClass} htmlFor="resume">
              Resume used
            </label>
            <input
              id="resume"
              list="resume-options"
              value={values.resume}
              onChange={update('resume')}
              placeholder="Pick a previous resume or type a new name"
              className={fieldClass}
            />
            <datalist id="resume-options">
              {resumes.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              {resumes.length} resume name{resumes.length === 1 ? '' : 's'} in your history
            </p>
          </div>

          <div>
            <label className={labelClass} htmlFor="salary">
              Salary range
            </label>
            <input
              id="salary"
              value={values.salary}
              onChange={update('salary')}
              placeholder="₹25-30 LPA or $150-180K"
              className={fieldClass}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="notes">
              Notes
            </label>
            <textarea
              id="notes"
              rows={4}
              value={values.notes}
              onChange={update('notes')}
              placeholder="Recruiter name, referral info, next steps..."
              className={`${fieldClass} resize-y`}
            />
          </div>
        </div>

        <footer className="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3.5 dark:border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-500/40 focus:outline-none"
          >
            {isEdit ? 'Save changes' : 'Add job'}
          </button>
        </footer>
      </form>
    </div>
  )
}
