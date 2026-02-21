import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import { CountriesService, type CountryPublic } from "@/client"
import { DataTable } from "@/components/Common/DataTable"

const columns: ColumnDef<CountryPublic>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => row.original.name || "-",
  },
  {
    accessorKey: "ioc",
    header: "IOC",
    cell: ({ row }) => row.original.ioc || "-",
  },
  {
    accessorKey: "file_flag",
    header: "Flag",
    cell: ({ row }) => row.original.file_flag || "-",
  },
]

export const Route = createFileRoute("/_layout/countries")({
  component: Countries,
  head: () => ({
    meta: [
      {
        title: "Countries - FastAPI Cloud",
      },
    ],
  }),
})

function CountriesTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const { data } = useQuery({
    queryFn: () =>
      CountriesService.readCountries({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
      }),
    queryKey: ["countries", pagination.pageIndex, pagination.pageSize],
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

function Countries() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Countries</h1>
        <p className="text-muted-foreground">Browse country records</p>
      </div>
      <CountriesTableContent />
    </div>
  )
}
