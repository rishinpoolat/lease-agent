import { faArrowRight, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { api } from "@/lib/api";

const statusPill: Record<string, string> = {
  available: "bg-muted text-muted-foreground",
  occupied: "bg-pass/10 text-pass",
};

export default async function UnitsPage() {
  const units = await api.listUnits();

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">Units</h1>
        <Link href="/leases/upload" className={buttonVariants({ size: "sm" })} data-icon="inline-start">
          <FontAwesomeIcon icon={faPlus} className="h-3 w-3" />
          Upload a lease
        </Link>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Building</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {units.map((u) => (
              <tr key={u.unit_id} className="hover:bg-muted/40">
                <td className="px-4 py-3">
                  <Link href={`/units/${u.unit_id}`} className="font-medium text-primary hover:underline">
                    {u.label}
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{u.building_name}</td>
                <td className="px-4 py-3 text-muted-foreground">{u.type}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ${
                      statusPill[u.status] ?? "bg-muted text-muted-foreground"
                    }`}
                  >
                    {u.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <Link href={`/units/${u.unit_id}`} className="text-muted-foreground hover:text-primary">
                    <FontAwesomeIcon icon={faArrowRight} className="h-3.5 w-3.5" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
