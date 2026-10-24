# Job Tracker

A local-first Kanban board for tracking job applications. Everything lives in your browser's
IndexedDB — no backend, no accounts, no network calls.

## Stack

- React 19 (function components + hooks) on Vite
- Tailwind CSS v4
- [`idb`](https://www.npmjs.com/package/idb) for the IndexedDB wrapper
- [`@dnd-kit`](https://dndkit.com/) for drag-and-drop

## Getting started

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production bundle in dist/
npm run preview  # serve the production build
npm run lint     # oxlint
```

> If your shell has `NODE_ENV=production` exported, npm skips dev dependencies. Install with
> `npm install --include=dev` in that case.

## Features

- **Kanban columns** — Wishlist, Applied, Follow-up, Interview, Offer, Rejected, each with a live
  card count and its own scroll area.
- **Drag and drop** — move cards between columns or reorder within a column (mouse or touch; the
  drop commits the new status and position to IndexedDB immediately). Keyboard users move a card by
  opening it and changing the **Status** field.
- **Add / edit** — a slide-over form with required-field validation (company and job title, plus
  URL format when a link is supplied).
- **Delete with confirmation** — no accidental data loss.
- **Search** — filter by company name or role. Dragging pauses while a filter is active so drop
  positions stay unambiguous.
- **Per-column date sort** — toggle newest/oldest first; the resulting order is persisted.
- **Resume history** — the resume field suggests every resume name you have used before.
- **Light/dark mode** — follows your system preference on first load, then remembers your choice.
- **JSON export / import** — back up the whole board, or restore a backup (imports merge by job id,
  so re-importing the same file is safe).

## Data model

Each record in the `jobs` object store (keyed by `id`, indexed on `status` and `createdAt`):

| Field         | Type   | Notes                                      |
| ------------- | ------ | ------------------------------------------ |
| `id`          | string | UUID generated in the browser              |
| `company`     | string | Required                                   |
| `title`       | string | Required                                   |
| `url`         | string | LinkedIn job URL, clickable on the card    |
| `resume`      | string | Resume used, e.g. `SDE_Resume_v3`          |
| `dateApplied` | string | `YYYY-MM-DD`, defaults to today, editable  |
| `salary`      | string | Optional, free text such as `₹25-30 LPA`   |
| `notes`       | string | Optional — recruiter, referral, next steps |
| `status`      | enum   | One of the six column ids                  |
| `order`       | number | Position within its column                 |
| `createdAt`   | string | ISO timestamp                              |
| `updatedAt`   | string | ISO timestamp                              |

## Project layout

```
src/
  App.jsx              layout, search state, export/import wiring
  constants.js         columns, status accents, default resume names
  db.js                IndexedDB open/read/write helpers
  hooks/useJobs.js     CRUD, ordering, drag commit, import/export
  hooks/useTheme.js    dark mode toggle
  lib/dates.js         date parsing, formatting, "days ago" labels
  lib/jobs.js          record normalising, ordering, move and sort logic
  components/          Board, Column, JobCard, JobForm, ConfirmDialog, Toolbar, Icons
```

## Notes

- IndexedDB is per-origin and per-browser, so the board is not synced across devices. Use
  **Export** to move data between machines.
- Clearing site data for the origin wipes the board — export a backup first.
