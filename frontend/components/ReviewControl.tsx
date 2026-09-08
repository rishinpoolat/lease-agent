"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
      <div className="flex flex-nowrap items-center gap-1.5 whitespace-nowrap">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoFocus
          className="w-32"
        />
        <Button
          size="sm"
          variant="success"
          onClick={() => {
            onEdit?.(draft);
            setEditing(false);
          }}
        >
          Save
        </Button>
        <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
          Cancel
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-nowrap items-center gap-1.5 whitespace-nowrap">
      <StatusBadge value={status} />
      <Button size="sm" variant="success" onClick={onAccept} disabled={status === "accepted"}>
        Accept
      </Button>
      <Button size="sm" variant="destructive" onClick={onReject} disabled={status === "rejected"}>
        Reject
      </Button>
      {onEdit && (
        <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
          Edit
        </Button>
      )}
    </div>
  );
}
