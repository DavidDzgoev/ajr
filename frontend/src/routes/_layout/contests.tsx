import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type ContestPublic, ContestsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<ContestPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "id_competition",
    header: "Competition ID",
    cell: ({ row }) => row.original.id_competition ?? "-",
  },
  {
    accessorKey: "id_judoka_blue",
    header: "Blue",
    cell: ({ row }) => row.original.id_judoka_blue ?? "-",
  },
  {
    accessorKey: "id_judoka_white",
    header: "White",
    cell: ({ row }) => row.original.id_judoka_white ?? "-",
  },
  {
    accessorKey: "id_winner",
    header: "Winner",
    cell: ({ row }) => row.original.id_winner ?? "-",
  },
  {
    accessorKey: "weight",
    header: "Weight",
    cell: ({ row }) => row.original.weight || "-",
  },
]

export const Route = createFileRoute("/_layout/contests")({
  component: Contests,
  head: () => ({
    meta: [
      {
        title: "Contests - FastAPI Cloud",
      },
    ],
  }),
})

function ContestsTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      ContestsService.readContests({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["contests", pagination.pageIndex, pagination.pageSize],
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

function Contests() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Contests</h1>
        <p className="text-muted-foreground">Browse contest records</p>
      </div>
      <ContestsTableContent />
    </div>
  )
}
