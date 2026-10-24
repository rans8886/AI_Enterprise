import { openDB } from 'idb'

const DB_NAME = 'job-tracker'
const DB_VERSION = 1
const JOBS_STORE = 'jobs'

let dbPromise = null

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(JOBS_STORE)) {
          const store = db.createObjectStore(JOBS_STORE, { keyPath: 'id' })
          store.createIndex('status', 'status', { unique: false })
          store.createIndex('createdAt', 'createdAt', { unique: false })
        }
      },
    })
  }
  return dbPromise
}

export async function getAllJobs() {
  const db = await getDB()
  return db.getAll(JOBS_STORE)
}

export async function putJob(job) {
  const db = await getDB()
  await db.put(JOBS_STORE, job)
  return job
}

export async function putJobs(jobs) {
  if (!jobs.length) return
  const db = await getDB()
  const tx = db.transaction(JOBS_STORE, 'readwrite')
  await Promise.all([
    ...jobs.map((job) => tx.store.put(job)),
    tx.done,
  ])
}

export async function deleteJob(id) {
  const db = await getDB()
  await db.delete(JOBS_STORE, id)
}

export async function replaceAllJobs(jobs) {
  const db = await getDB()
  const tx = db.transaction(JOBS_STORE, 'readwrite')
  await tx.store.clear()
  for (const job of jobs) {
    await tx.store.put(job)
  }
  await tx.done
}
