"use client";

import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

/** The one occupancy-mutating action in the app -- see
 * docs/context/06-human-in-the-loop-ux.md. Confirmation is deliberate here
 * and nowhere else: this is a write to Unit.status, not just a review_status
 * change. */
export function AcceptUnitMatchCard({ leaseId, unitLabel }: { leaseId: string; unitLabel: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function handleAccept() {
    if (!confirm(`Mark ${unitLabel} as occupied by this lease? This cannot be undone from here.`)) {
      return;
    }
    setPending(true);
    try {
      await api.acceptUnitMatch(leaseId);
      router.refresh();
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
      <FontAwesomeIcon icon={faTriangleExclamation} className="mt-0.5 h-4 w-4 shrink-0 text-warn" />
      <div className="flex-1">
        <p className="text-sm text-gray-800">
          This lease was matched to <strong>{unitLabel}</strong> but the match hasn&apos;t been
          accepted yet. Accepting it is the only action that can flip the unit to occupied (and
          only if rule R7 passes).
        </p>
        <Button
          size="sm"
          onClick={handleAccept}
          disabled={pending}
          className="mt-3 bg-amber-700 text-white hover:bg-amber-800"
        >
          {pending ? "Accepting..." : "Accept unit match"}
        </Button>
      </div>
    </div>
  );
}
