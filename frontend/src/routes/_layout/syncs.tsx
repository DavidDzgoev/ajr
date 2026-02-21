import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type DataSyncPublic, SyncService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<DataSyncPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "sync_type",
    header: "Type",
    cell: ({ row }) => row.original.sync_type,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => row.original.status,
  },
  {
    accessorKey: "started_at",
    header: "Started",
    cell: ({ row }) => new Date(row.original.started_at).toLocaleString(),
  },
  {
    accessorKey: "completed_at",
    header: "Completed",
    cell: ({ row }) =>
      row.original.completed_at
        ? new Date(row.original.completed_at).toLocaleString()
        : "-",
  },
]

export const Route = createFileRoute("/_layout/syncs")({
  component: Syncs,
  head: () => ({
    meta: [
      {
        title: "Data Syncs - FastAPI Cloud",
      },
    ],
  }),
})

function SyncsTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      SyncService.readSyncHistory({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["syncs", pagination.pageIndex, pagination.pageSize],
    placeholderData: keepPreviousData,
  })

  return (
    <DataTable
      columns={columns}
      data={data?.data ?? []}
      serverPagination={{
        pagination,
        rowCount: data?.count ?? 0,
        onPaginationChange: setPagination,
      }}
    />
  )
}

function Syncs() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Data Syncs</h1>
        <p className="text-muted-foreground">Browse synchronization history</p>
      </div>
      <SyncsTableContent />
    </div>
  )
}
