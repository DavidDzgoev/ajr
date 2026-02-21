import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import { useState } from "react"

import {
  RatingFormulasService,
  type RatingPublic,
  RatingsService,
} from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const parseOptionalNumber = (value: string): number | undefined => {
  if (!value.trim()) {
    return undefined
  }
  const num = Number(value)
  return Number.isFinite(num) ? num : undefined
}

const buildColumns = (
  formulaNamesById: Record<string, string>,
): ColumnDef<RatingPublic>[] => [
  { accessorKey: "id", header: "ID" },
  {
    id: "judoka_name",
    header: "Judoka",
    cell: ({ row }) => {
      const family = row.original.judoka_family_name || ""
      const given = row.original.judoka_given_name || ""
      return `${family} ${given}`.trim() || "-"
    },
  },
  {
    accessorKey: "id_judoka",
    header: "Judoka ID",
    cell: ({ row }) => row.original.id_judoka ?? "-",
  },
  {
    accessorKey: "weight",
    header: "Weight",
    cell: ({ row }) => row.original.weight || "-",
  },
  {
    accessorKey: "formula_id",
    header: "Formula",
    cell: ({ row }) => {
      const formulaId = row.original.formula_id
      if (!formulaId) {
        return "-"
      }
      return formulaNamesById[formulaId] || formulaId
    },
  },
  {
    accessorKey: "rating_value",
    header: "Rating",
    cell: ({ row }) => row.original.rating_value?.toFixed(2) || "-",
  },
]

export const Route = createFileRoute("/_layout/ratings")({
  component: Ratings,
  head: () => ({
    meta: [
      {
        title: "Ratings - FastAPI Cloud",
      },
    ],
  }),
})

function RatingsTableContent() {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 25 })
  const [filters, setFilters] = useState({
    surname: "",
    judokaId: "",
    weight: "",
    ratingMin: "",
    formulaId: "all",
  })
  const [appliedFilters, setAppliedFilters] = useState(filters)

  const { data: formulasData } = useQuery({
    queryFn: () =>
      RatingFormulasService.readRatingFormulas({
        limit: 1000,
        skip: 0,
        isActive: true,
      }),
    queryKey: ["rating-formulas", "active", "all"],
  })

  const formulaNamesById = Object.fromEntries(
    (formulasData?.data ?? []).map((formula) => [formula.id, formula.name]),
  )

  const columns = buildColumns(formulaNamesById)

  const { data } = useQuery({
    queryFn: () =>
      RatingsService.readRatings({
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
        surname: appliedFilters.surname || undefined,
        judokaId: parseOptionalNumber(appliedFilters.judokaId),
        weight: appliedFilters.weight || undefined,
        ratingMin: parseOptionalNumber(appliedFilters.ratingMin),
        formulaId:
          appliedFilters.formulaId !== "all"
            ? appliedFilters.formulaId
            : undefined,
      }),
    queryKey: [
      "ratings",
      pagination.pageIndex,
      pagination.pageSize,
      appliedFilters.surname,
      appliedFilters.judokaId,
      appliedFilters.weight,
      appliedFilters.ratingMin,
      appliedFilters.formulaId,
    ],
    placeholderData: keepPreviousData,
  })

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
        <Input
          placeholder="Surname"
          value={filters.surname}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, surname: e.target.value }))
          }
        />
        <Input
          placeholder="Judoka ID"
          value={filters.judokaId}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, judokaId: e.target.value }))
          }
        />
        <Input
          placeholder="Weight"
          value={filters.weight}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, weight: e.target.value }))
          }
        />
        <Input
          placeholder="Min rating"
          value={filters.ratingMin}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, ratingMin: e.target.value }))
          }
        />
        <Select
          value={filters.formulaId}
          onValueChange={(value) =>
            setFilters((prev) => ({ ...prev, formulaId: value }))
          }
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Formula" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All formulas</SelectItem>
            {(formulasData?.data ?? []).map((formula) => (
              <SelectItem key={formula.id} value={formula.id}>
                {formula.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex gap-2">
        <Button
          onClick={() => {
            setPagination((prev) => ({ ...prev, pageIndex: 0 }))
            setAppliedFilters(filters)
          }}
        >
          Search
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            const reset = {
              surname: "",
              judokaId: "",
              weight: "",
              ratingMin: "",
              formulaId: "all",
            }
            setFilters(reset)
            setAppliedFilters(reset)
            setPagination((prev) => ({ ...prev, pageIndex: 0 }))
          }}
        >
          Reset
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        serverPagination={{
          pagination,
          rowCount: data?.count ?? 0,
          onPaginationChange: setPagination,
        }}
      />
    </div>
  )
}

function Ratings() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ratings</h1>
        <p className="text-muted-foreground">
          Browse current ratings (sorted from highest to lowest)
        </p>
      </div>
      <RatingsTableContent />
    </div>
  )
}
