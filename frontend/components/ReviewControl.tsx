"use client";

import { useState } from "react";

import type { ReviewStatus } from "@/lib/types";

interface Props {
  status: ReviewStatus;
  onAccept: () => void;
  onReject: () => void;
  onEdit?: (value: string) => void;
  currentValue?: string;
}

/** One shared accept/reject/edit control, used for LeaseField, Flag, and
 * WorkOrder alike -- see docs/context/06-human-in-the-loop-ux.md. Reject is
 * always non-destructive: it only changes review_status, never deletes. */
export function ReviewControl({ status, onAccept, onReject, onEdit, currentValue }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(currentValue ?? "");

  if (editing) {
    return (
      <div className="review-control">
        <input value={draft} onChange={(e) => setDraft(e.target.value)} autoFocus />
        <button
          onClick={() => {
            onEdit?.(draft);
            setEditing(false);
          }}
        >
          Save
        </button>
        <button onClick={() => setEditing(false)}>Cancel</button>
      </div>
    );
  }

  return (
    <div className="review-control">
      <span className={`badge badge-${status}`}>{status}</span>
      <button onClick={onAccept} disabled={status === "accepted"}>
        Accept
      </button>
      <button onClick={onReject} disabled={status === "rejected"}>
        Reject
      </button>
      {onEdit && <button onClick={() => setEditing(true)}>Edit</button>}
    </div>
  );
}
