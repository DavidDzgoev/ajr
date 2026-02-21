import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type CompetitionPublic, CompetitionsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<CompetitionPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => row.original.name || "-",
  },
  {
    accessorKey: "date_from",
    header: "Date From",
    cell: ({ row }) => row.original.date_from || "-",
  },
  {
    accessorKey: "date_to",
    header: "Date To",
    cell: ({ row }) => row.original.date_to || "-",
  },
  {
    accessorKey: "city",
    header: "City",
    cell: ({ row }) => row.original.city || "-",
  },
]

export const Route = createFileRoute("/_layout/competitions")({
  component: Competitions,
  head: () => ({
    meta: [
      {
        title: "Competitions - FastAPI Cloud",
      },
    ],
  }),
})

function CompetitionsTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      CompetitionsService.readCompetitions({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["competitions", pagination.pageIndex, pagination.pageSize],
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

function Competitions() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Competitions</h1>
        <p className="text-muted-foreground">Browse competition records</p>
      </div>
      <CompetitionsTableContent />
    </div>
  )
}
