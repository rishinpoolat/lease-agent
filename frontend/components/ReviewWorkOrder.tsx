"use client";

import { useRouter } from "next/navigation";

import { ReviewControl } from "@/components/ReviewControl";
import { api } from "@/lib/api";
import type { WorkOrder } from "@/lib/types";

/** Thin client island wrapping ReviewControl for a single WorkOrder -- see
 * components/ReviewField.tsx for the pattern. */
export function ReviewWorkOrder({ workOrder }: { workOrder: WorkOrder }) {
  const router = useRouter();

  return (
    <ReviewControl
      status={workOrder.review_status}
      onAccept={() => api.reviewWorkOrder(workOrder.id, "accept").then(() => router.refresh())}
      onReject={() => api.reviewWorkOrder(workOrder.id, "reject").then(() => router.refresh())}
    />
  );
}
