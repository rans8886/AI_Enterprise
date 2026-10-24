import { useEffect } from 'react'
import { WarningIcon } from './Icons'

export default function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Delete',
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onCancel])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fade-in absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
        onClick={onCancel}
        aria-hidden="true"
      />
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="fade-in relative w-full max-w-sm rounded-xl border border-slate-200 bg-white p-5 shadow-xl dark:border-slate-800 dark:bg-slate-900"
      >
        <div className="flex gap-3">
          <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-400">
            <WarningIcon />
          </span>
          <div className="min-w-0">
            <h2
              id="confirm-title"
              className="text-sm font-semibold text-slate-900 dark:text-slate-100"
            >
              {title}
            </h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{message}</p>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            type="button"
            autoFocus
            onClick={onConfirm}
            className="rounded-lg bg-rose-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-rose-500 focus:ring-2 focus:ring-rose-500/40 focus:outline-none"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
