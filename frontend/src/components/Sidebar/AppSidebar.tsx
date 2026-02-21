import {
  ArrowUpDown,
  Award,
  Building2,
  Command,
  Flag,
  Home,
  RefreshCw,
  ShieldHalf,
  Swords,
  UserSquare2,
} from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: Flag, title: "Countries", path: "/countries" },
  { icon: UserSquare2, title: "Judokas", path: "/judokas" },
  { icon: Building2, title: "Competitions", path: "/competitions" },
  { icon: Swords, title: "Contests", path: "/contests" },
  { icon: Award, title: "Ratings", path: "/ratings" },
  { icon: ShieldHalf, title: "Formulas", path: "/rating-formulas" },
  { icon: ArrowUpDown, title: "Rating Changes", path: "/rating-changes" },
  { icon: RefreshCw, title: "Sync History", path: "/syncs" },
]

const superuserOnlyItems: Item[] = [
  { icon: Command, title: "Commands", path: "/commands" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const items = currentUser?.is_superuser
    ? [...baseItems, ...superuserOnlyItems]
    : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
