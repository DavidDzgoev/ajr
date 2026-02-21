import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { type JudokaPublic, JudokasService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<JudokaPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    id: "name",
    header: "Name",
    cell: ({ row }) =>
      `${row.original.family_name || ""} ${row.original.given_name || ""}`.trim() ||
      "-",
  },
  {
    accessorKey: "gender",
    header: "Gender",
    cell: ({ row }) => row.original.gender || "-",
  },
  {
    accessorKey: "dob_year",
    header: "DOB Year",
    cell: ({ row }) => row.original.dob_year ?? "-",
  },
  {
    accessorKey: "id_country",
    header: "Country ID",
    cell: ({ row }) => row.original.id_country ?? "-",
  },
]

export const Route = createFileRoute("/_layout/judokas")({
  component: Judokas,
  head: () => ({
    meta: [
      {
        title: "Judokas - FastAPI Cloud",
      },
    ],
  }),
})

function JudokasTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      JudokasService.readJudokas({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["judokas", pagination.pageIndex, pagination.pageSize],
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

function Judokas() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Judokas</h1>
        <p className="text-muted-foreground">Browse athlete records</p>
      </div>
      <JudokasTableContent />
    </div>
  )
}
