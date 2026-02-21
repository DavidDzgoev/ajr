import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type RatingFormulaPublic, RatingFormulasService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<RatingFormulaPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => row.original.name,
  },
  {
    accessorKey: "is_active",
    header: "Active",
    cell: ({ row }) => (row.original.is_active ? "Yes" : "No"),
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => row.original.description || "-",
  },
]

export const Route = createFileRoute("/_layout/rating-formulas")({
  component: RatingFormulas,
  head: () => ({
    meta: [
      {
        title: "Rating Formulas - FastAPI Cloud",
      },
    ],
  }),
})

function RatingFormulasTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      RatingFormulasService.readRatingFormulas({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["rating-formulas", pagination.pageIndex, pagination.pageSize],
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

function RatingFormulas() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Rating Formulas</h1>
        <p className="text-muted-foreground">Browse rating formulas</p>
      </div>
      <RatingFormulasTableContent />
    </div>
  )
}
