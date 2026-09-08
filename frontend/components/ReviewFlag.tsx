"use client";

import { useRouter } from "next/navigation";

import { ReviewControl } from "@/components/ReviewControl";
import { api } from "@/lib/api";
import type { Flag } from "@/lib/types";

/** Thin client island wrapping ReviewControl for a single Flag -- see
 * components/ReviewField.tsx for the pattern. */
export function ReviewFlag({ flag }: { flag: Flag }) {
  const router = useRouter();

  return (
    <ReviewControl
      status={flag.review_status}
      onAccept={() => api.reviewFlag(flag.id, "accept").then(() => router.refresh())}
      onReject={() => api.reviewFlag(flag.id, "reject").then(() => router.refresh())}
    />
  );
}
