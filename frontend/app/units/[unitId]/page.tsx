"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";

import { ReviewControl } from "@/components/ReviewControl";
import { api } from "@/lib/api";
import type { UnitDetail } from "@/lib/types";

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function UnitDetailPage({ params }: { params: Promise<{ unitId: string }> }) {
  const { unitId } = use(params);
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api.getUnit(unitId).then(setUnit).catch((e) => setError(String(e)));
  }, [unitId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (error) return <p style={{ color: "var(--fail)" }}>{error}</p>;
  if (!unit) return <p>Loading...</p>;

  const lease = unit.lease;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>
          {unit.label} <span className="unit-status">({unit.status})</span>
        </h1>
        <Link className="unit-link" href={`/units/${unitId}/upload-photos`}>
          + Report an issue
        </Link>
      </div>
      <p style={{ color: "var(--muted)" }}>
        {unit.property_name} / {unit.building_name} / {unit.type}
      </p>

      {/* Lease panel */}
      <section className="card">
        <h2>Lease</h2>
        {!lease && (
          <p>
            No lease uploaded for this unit yet.{" "}
            <Link className="unit-link" href="/leases/upload">Upload one</Link>.
          </p>
        )}

        {lease && (
          <>
            <p style={{ color: "var(--muted)" }}>
              Uploaded {new Date(lease.uploaded_at).toLocaleString()} from{" "}
              <code>{lease.source_file_ref}</code>
            </p>

            {!lease.unit_match_accepted && (
              <div className="card" style={{ background: "#fffbea" }}>
                <p>
                  This lease was matched to <strong>{unit.label}</strong> but the match hasn&apos;t been
                  accepted yet. Accepting it is the only action that can flip the unit to occupied
                  (and only if rule R7 passes).
                </p>
                <button
                  onClick={async () => {
                    await api.acceptUnitMatch(lease.id);
                    refresh();
                  }}
                >
                  Accept unit match
                </button>
              </div>
            )}

            <h3>Extracted fields</h3>
            <table>
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Confidence</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {lease.fields.map((f) => (
                  <tr key={f.id}>
                    <td>{f.field_name}</td>
                    <td>
                      {displayValue(f.review_status === "edited" ? f.edited_value : f.value)}
                      {f.review_status === "edited" && (
                        <div className="source-excerpt">originally: {displayValue(f.value)}</div>
                      )}
                      {f.source_excerpt && <div className="source-excerpt">&ldquo;{f.source_excerpt}&rdquo;</div>}
                    </td>
                    <td>{f.confidence}</td>
                    <td>
                      <ReviewControl
                        status={f.review_status}
                        currentValue={displayValue(f.value)}
                        onAccept={() => api.reviewLeaseField(f.id, "accept").then(refresh)}
                        onReject={() => api.reviewLeaseField(f.id, "reject").then(refresh)}
                        onEdit={(v) => api.reviewLeaseField(f.id, "edit", v).then(refresh)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3>Rule validation ({lease.rule_evaluations.length ? "owner_ruleset.json" : "pending"})</h3>
            <table>
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Verdict</th>
                  <th>Reason</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {lease.rule_evaluations.map((r) => (
                  <tr key={r.id}>
                    <td>{r.rule_id}</td>
                    <td>
                      <span className={`badge badge-${r.verdict}`}>{r.verdict}</span>
                    </td>
                    <td>{r.reason}</td>
                    <td>{r.severity}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {lease.flags.length > 0 && (
              <>
                <h3>Flags</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Description</th>
                      <th>Severity</th>
                      <th>Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lease.flags.map((fl) => (
                      <tr key={fl.id}>
                        <td>{fl.field_name ?? "(document-level)"}</td>
                        <td>{fl.description}</td>
                        <td>{fl.severity}</td>
                        <td>
                          <ReviewControl
                            status={fl.review_status}
                            onAccept={() => api.reviewFlag(fl.id, "accept").then(refresh)}
                            onReject={() => api.reviewFlag(fl.id, "reject").then(refresh)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </>
        )}
      </section>

      {/* Issues panel */}
      <section className="card">
        <h2>Reported issues</h2>
        {unit.photo_reports.length === 0 && <p>No issues reported for this unit yet.</p>}
        {unit.photo_reports.map((pr) => (
          <div key={pr.id} className="card">
            <p style={{ color: "var(--muted)" }}>
              Reported {new Date(pr.uploaded_at).toLocaleString()} -- {pr.photo_refs.length} photo(s)
            </p>
            <p>{pr.condition_assessment ?? "Processing..."}</p>
            {pr.detected_contents.length > 0 && (
              <p>
                <strong>Contents:</strong> {pr.detected_contents.join(", ")}
              </p>
            )}
            {pr.work_orders.map((wo) => (
              <div key={wo.id} className="card" style={{ background: "#fff8f0" }}>
                <strong>{wo.title}</strong>
                <p>{wo.description}</p>
                <p>Severity: {wo.severity}</p>
                <ReviewControl
                  status={wo.review_status}
                  onAccept={() => api.reviewWorkOrder(wo.id, "accept").then(refresh)}
                  onReject={() => api.reviewWorkOrder(wo.id, "reject").then(refresh)}
                />
              </div>
            ))}
          </div>
        ))}
      </section>
    </div>
  );
}
