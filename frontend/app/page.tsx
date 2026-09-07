"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { UnitSummary } from "@/lib/types";

export default function UnitsPage() {
  const [units, setUnits] = useState<UnitSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listUnits().then(setUnits).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Units</h1>
        <Link href="/leases/upload" className="unit-link">
          + Upload a lease
        </Link>
      </div>

      {error && <p style={{ color: "var(--fail)" }}>{error}</p>}
      {!units && !error && <p>Loading...</p>}

      {units && (
        <table>
          <thead>
            <tr>
              <th>Unit</th>
              <th>Building</th>
              <th>Type</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {units.map((u) => (
              <tr key={u.unit_id}>
                <td>
                  <Link className="unit-link" href={`/units/${u.unit_id}`}>
                    {u.label}
                  </Link>
                </td>
                <td>{u.building_name}</td>
                <td>{u.type}</td>
                <td className="unit-status">{u.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
