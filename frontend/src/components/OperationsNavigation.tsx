import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ChartNoAxesCombined,
  HeartPulse,
  Clapperboard,
  FileChartColumn,
  SlidersHorizontal,
  MessagesSquare,
} from "lucide-react";
import { useLocale } from "../hooks/useLocale";
export function OperationsNavigation() {
  const { w } = useLocale();
  return (
    <nav className="ops-tabs" aria-label={w("Operations Sections")}>
      {(
        [
          ["", "Overview", LayoutDashboard],
          ["insights", "Journey Insights", ChartNoAxesCombined],
          ["health", "System Health", HeartPulse],
          ["archive", "Replay Archive", Clapperboard],
          ["reports", "Quarterly Reports", FileChartColumn],
          ["settings", "Operational Settings", SlidersHorizontal],
        ] as const
      ).map(([path, label, Icon]) => (
        <NavLink
          end
          key={path}
          to={"/admin/operations" + (path ? "/" + path : "")}
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <Icon size={20} />
          <span>{w(label)}</span>
        </NavLink>
      ))}
      <NavLink
        to="/admin/support"
        className={({ isActive }) => (isActive ? "active" : "")}
      >
        <MessagesSquare size={20} />
        <span>{w("User Support")}</span>
      </NavLink>
    </nav>
  );
}
