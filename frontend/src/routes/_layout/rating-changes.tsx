import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type RatingChangePublic, RatingChangesService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<RatingChangePublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "id_judoka",
    header: "Judoka ID",
    cell: ({ row }) => row.original.id_judoka ?? "-",
  },
  {
    accessorKey: "id_contest",
    header: "Contest ID",
    cell: ({ row }) => row.original.id_contest ?? "-",
  },
  {
    accessorKey: "id_opponent",
    header: "Opponent ID",
    cell: ({ row }) => row.original.id_opponent ?? "-",
  },
  {
    accessorKey: "rating_change",
    header: "Delta",
    cell: ({ row }) => row.original.rating_change?.toFixed(2) || "-",
  },
]

export const Route = createFileRoute("/_layout/rating-changes")({
  component: RatingChanges,
  head: () => ({
    meta: [
      {
        title: "Rating Changes - FastAPI Cloud",
      },
    ],
  }),
})

function RatingChangesTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      RatingChangesService.readRatingChanges({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["rating-changes", pagination.pageIndex, pagination.pageSize],
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

function RatingChanges() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Rating Changes</h1>
        <p className="text-muted-foreground">Browse rating change history</p>
      </div>
      <RatingChangesTableContent />
    </div>
  )
}
