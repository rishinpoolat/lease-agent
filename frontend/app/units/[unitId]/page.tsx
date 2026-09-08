import { faCamera, faFileLines, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { Metadata } from "next";
import Link from "next/link";

import { AcceptUnitMatchCard } from "@/components/AcceptUnitMatchCard";
import { ReviewField } from "@/components/ReviewField";
import { ReviewFlag } from "@/components/ReviewFlag";
import { ReviewWorkOrder } from "@/components/ReviewWorkOrder";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { api } from "@/lib/api";
import { displayValue } from "@/lib/format";

type Params = { params: Promise<{ unitId: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { unitId } = await params;
  const unit = await api.getUnit(unitId);
  return { title: `${unit.label} · Lease Agent` };
}

export default async function UnitDetailPage({ params }: Params) {
  const { unitId } = await params;
  const unit = await api.getUnit(unitId);
  const lease = unit.lease;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">
          {unit.label}{" "}
          <span className="ml-1 align-middle text-xs font-semibold uppercase text-muted-foreground">
            ({unit.status})
          </span>
        </h1>
        <Link href={`/units/${unitId}/upload-photos`} className={buttonVariants({ size: "sm" })}>
          <FontAwesomeIcon icon={faPlus} className="h-3 w-3" />
          Report an issue
        </Link>
      </div>
      <p className="mb-5 text-sm text-muted-foreground">
        {unit.property_name} / {unit.building_name} / {unit.type}
      </p>

      {/* Lease panel */}
      <Card className="mb-4 px-5">
        <CardHeader className="px-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <FontAwesomeIcon icon={faFileLines} className="h-4 w-4 text-primary" />
            Lease
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          {!lease && (
            <p className="text-sm text-muted-foreground">
              No lease uploaded for this unit yet.{" "}
              <Link className="text-primary hover:underline" href="/leases/upload">
                Upload one
              </Link>
              .
            </p>
          )}

          {lease && (
            <>
              <p className="mb-4 text-xs text-muted-foreground">
                Uploaded {new Date(lease.uploaded_at).toLocaleString()} from{" "}
                <code className="rounded bg-muted px-1 py-0.5">{lease.source_file_ref}</code>
              </p>

              {!lease.unit_match_accepted && (
                <div className="mb-4">
                  <AcceptUnitMatchCard leaseId={lease.id} unitLabel={unit.label} />
                </div>
              )}

              <h3 className="mb-2 text-sm font-semibold text-foreground">Extracted fields</h3>
              <div className="mb-5 overflow-x-auto rounded-md border border-border">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Field</th>
                      <th className="px-3 py-2 font-medium">Value</th>
                      <th className="px-3 py-2 font-medium">Confidence</th>
                      <th className="w-56 px-3 py-2 font-medium">Review</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {lease.fields.map((f) => (
                      <tr key={f.id}>
                        <td className="px-3 py-2 font-medium text-foreground">{f.field_name}</td>
                        <td className="px-3 py-2">
                          {displayValue(f.review_status === "edited" ? f.edited_value : f.value)}
                          {f.review_status === "edited" && (
                            <div className="mt-0.5 text-xs italic text-muted-foreground">
                              originally: {displayValue(f.value)}
                            </div>
                          )}
                          {f.source_excerpt && (
                            <div className="mt-0.5 text-xs italic text-muted-foreground">
                              &ldquo;{f.source_excerpt}&rdquo;
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground">{f.confidence}</td>
                        <td className="px-3 py-2">
                          <ReviewField field={f} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <h3 className="mb-2 text-sm font-semibold text-foreground">
                Rule validation ({lease.rule_evaluations.length ? "owner_ruleset.json" : "pending"})
              </h3>
              <div
                className={`overflow-x-auto rounded-md border border-border ${lease.flags.length > 0 ? "mb-5" : ""}`}
              >
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Rule</th>
                      <th className="px-3 py-2 font-medium">Verdict</th>
                      <th className="px-3 py-2 font-medium">Reason</th>
                      <th className="px-3 py-2 font-medium">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {lease.rule_evaluations.map((r) => (
                      <tr key={r.id}>
                        <td className="px-3 py-2 font-medium text-foreground">{r.rule_id}</td>
                        <td className="px-3 py-2">
                          <StatusBadge value={r.verdict} />
                        </td>
                        <td className="px-3 py-2 text-muted-foreground">{r.reason}</td>
                        <td className="px-3 py-2 text-muted-foreground">{r.severity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {lease.flags.length > 0 && (
                <>
                  <h3 className="mb-2 text-sm font-semibold text-foreground">Flags</h3>
                  <div className="overflow-x-auto rounded-md border border-border">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                        <tr>
                          <th className="px-3 py-2 font-medium">Field</th>
                          <th className="px-3 py-2 font-medium">Description</th>
                          <th className="px-3 py-2 font-medium">Severity</th>
                          <th className="w-56 px-3 py-2 font-medium">Review</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {lease.flags.map((fl) => (
                          <tr key={fl.id}>
                            <td className="px-3 py-2 font-medium text-foreground">
                              {fl.field_name ?? "(document-level)"}
                            </td>
                            <td className="px-3 py-2 text-muted-foreground">{fl.description}</td>
                            <td className="px-3 py-2 text-muted-foreground">{fl.severity}</td>
                            <td className="px-3 py-2">
                              <ReviewFlag flag={fl} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Issues panel */}
      <Card className="px-5">
        <CardHeader className="px-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <FontAwesomeIcon icon={faCamera} className="h-4 w-4 text-primary" />
            Reported issues
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          {unit.photo_reports.length === 0 && (
            <p className="text-sm text-muted-foreground">No issues reported for this unit yet.</p>
          )}
          <div className="space-y-3">
            {unit.photo_reports.map((pr) => (
              <div key={pr.id} className="rounded-md border border-border p-4">
                <p className="mb-2 text-xs text-muted-foreground">
                  Reported {new Date(pr.uploaded_at).toLocaleString()} — {pr.photo_refs.length} photo(s)
                </p>
                <p className="text-sm text-foreground">{pr.condition_assessment ?? "Processing..."}</p>
                {pr.detected_contents.length > 0 && (
                  <p className="mt-1 text-sm text-foreground">
                    <strong>Contents:</strong> {pr.detected_contents.join(", ")}
                  </p>
                )}
                {pr.work_orders.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {pr.work_orders.map((wo) => (
                      <div key={wo.id} className="rounded-md border border-amber-200 bg-amber-50 p-3">
                        <strong className="text-sm text-foreground">{wo.title}</strong>
                        <p className="mt-0.5 text-sm text-foreground">{wo.description}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">Severity: {wo.severity}</p>
                        <div className="mt-2">
                          <ReviewWorkOrder workOrder={wo} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
