"use client";

import { useRouter } from "next/navigation";

import { ReviewControl } from "@/components/ReviewControl";
import { api } from "@/lib/api";
import { displayValue } from "@/lib/format";
import type { LeaseField } from "@/lib/types";

/** Thin client island wrapping ReviewControl for a single LeaseField -- owns
 * the mutation + router.refresh(), so the parent unit-detail page can stay a
 * plain Server Component instead of holding fetched state itself. */
export function ReviewField({ field }: { field: LeaseField }) {
  const router = useRouter();

  return (
    <ReviewControl
      status={field.review_status}
      currentValue={displayValue(field.value)}
      onAccept={() => api.reviewLeaseField(field.id, "accept").then(() => router.refresh())}
      onReject={() => api.reviewLeaseField(field.id, "reject").then(() => router.refresh())}
      onEdit={(v) => api.reviewLeaseField(field.id, "edit", v).then(() => router.refresh())}
    />
  );
}
