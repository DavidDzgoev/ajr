import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ShieldAlert } from "lucide-react"

import { SyncService } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/commands")({
  component: Commands,
  head: () => ({
    meta: [
      {
        title: "Commands - FastAPI Cloud",
      },
    ],
  }),
})

function Commands() {
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuth()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const triggerSyncMutation = useMutation({
    mutationFn: () => SyncService.triggerSync(),
    onSuccess: () => {
      showSuccessToast("Sync job started. Existing data will be replaced.")
      queryClient.invalidateQueries({ queryKey: ["syncs"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Commands</h1>
        <p className="text-muted-foreground">
          Run administrative commands for data maintenance
        </p>
      </div>

      {!currentUser?.is_superuser ? (
        <Alert variant="destructive">
          <ShieldAlert />
          <AlertTitle>Access denied</AlertTitle>
          <AlertDescription>
            Only superusers can run commands on this page.
          </AlertDescription>
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Full Sync: Reset and Recalculate Ratings</CardTitle>
            <CardDescription>
              Clears synced entities, reloads data from source, and recalculates
              all ratings from scratch.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <ShieldAlert />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                This operation is destructive and may take time. It replaces all
                current synced data.
              </AlertDescription>
            </Alert>
          </CardContent>
          <CardFooter className="justify-between gap-3">
            <LoadingButton
              loading={triggerSyncMutation.isPending}
              onClick={() => triggerSyncMutation.mutate()}
            >
              Run Full Sync
            </LoadingButton>
            <Link
              to="/syncs"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Open sync history
            </Link>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
