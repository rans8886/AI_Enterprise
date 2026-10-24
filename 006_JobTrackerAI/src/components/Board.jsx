import { useMemo, useRef, useState } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { COLUMNS } from '../constants'
import { JobCardView } from './JobCard'
import Column from './Column'

export default function Board({
  groups,
  dragDisabled,
  onBeginDrag,
  onMoveLocal,
  onEndDrag,
  onSortColumn,
  onAdd,
  onEdit,
  onDelete,
}) {
  const [activeId, setActiveId] = useState(null)
  const [sortDirs, setSortDirs] = useState({})
  const lastDragEndRef = useRef(0)

  // Pointer only: the keyboard sensor swallows Enter/Space on the card's own
  // edit and delete buttons, and its arrow-key getter cannot hop columns.
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  )

  const statusById = useMemo(() => {
    const map = new Map()
    for (const column of COLUMNS) {
      for (const job of groups[column.id] ?? []) {
        map.set(job.id, column.id)
      }
    }
    return map
  }, [groups])

  const activeJob = useMemo(() => {
    if (!activeId) return null
    for (const column of COLUMNS) {
      const match = (groups[column.id] ?? []).find((job) => job.id === activeId)
      if (match) return match
    }
    return null
  }, [activeId, groups])

  function handleDragStart({ active }) {
    setActiveId(active.id)
    onBeginDrag()
  }

  function resolveStatus(over) {
    return over.data.current?.type === 'column' ? over.id : statusById.get(over.id)
  }

  function handleDragOver({ active, over }) {
    if (!over) return
    const from = statusById.get(active.id)
    const to = resolveStatus(over)
    if (!from || !to || from === to) return
    const list = groups[to] ?? []
    const index =
      over.data.current?.type === 'column'
        ? list.length
        : Math.max(
            0,
            list.findIndex((job) => job.id === over.id),
          )
    onMoveLocal(active.id, to, index)
  }

  function handleDragEnd({ active, over }) {
    if (over) {
      const from = statusById.get(active.id)
      const to = resolveStatus(over)
      const isCard = over.data.current?.type === 'card'
      if (from && to && from === to && isCard && over.id !== active.id) {
        const list = groups[from] ?? []
        const index = list.findIndex((job) => job.id === over.id)
        if (index !== -1) onMoveLocal(active.id, from, index)
      }
    }
    lastDragEndRef.current = Date.now()
    setActiveId(null)
    onEndDrag()
  }

  function handleDragCancel() {
    lastDragEndRef.current = Date.now()
    setActiveId(null)
    onEndDrag()
  }

  // A drop also emits a click; ignore clicks that trail a drag so cards are
  // not opened for editing every time they are moved.
  function handleCardClick(job) {
    if (Date.now() - lastDragEndRef.current < 200) return
    onEdit(job)
  }

  function handleSortToggle(status) {
    const next = (sortDirs[status] ?? 'desc') === 'desc' ? 'asc' : 'desc'
    setSortDirs((prev) => ({ ...prev, [status]: next }))
    onSortColumn(status, next)
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex min-h-0 flex-1 gap-3 overflow-x-auto overflow-y-hidden pb-2">
        {COLUMNS.map((column) => (
          <Column
            key={column.id}
            column={column}
            jobs={groups[column.id] ?? []}
            sortDirection={sortDirs[column.id] ?? 'desc'}
            dragDisabled={dragDisabled}
            onSortToggle={() => handleSortToggle(column.id)}
            onAdd={onAdd}
            onEdit={onEdit}
            onDelete={onDelete}
            onCardClick={handleCardClick}
          />
        ))}
      </div>
      <DragOverlay dropAnimation={{ duration: 160, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' }}>
        {activeJob ? <JobCardView job={activeJob} overlay /> : null}
      </DragOverlay>
    </DndContext>
  )
}
