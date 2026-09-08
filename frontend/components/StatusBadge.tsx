import {
  faCircleCheck,
  faCircleXmark,
  faClock,
  faPen,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import type { ReviewStatus, Verdict } from "@/lib/types";

type BadgeValue = ReviewStatus | Verdict;

const CONFIG: Record<BadgeValue, { icon: typeof faClock; className: string }> = {
  pending: { icon: faClock, className: "bg-muted text-muted-foreground" },
  accepted: { icon: faCircleCheck, className: "bg-pass/10 text-pass" },
  edited: { icon: faPen, className: "bg-pass/10 text-pass" },
  rejected: { icon: faCircleXmark, className: "bg-fail/10 text-fail" },
  PASS: { icon: faCircleCheck, className: "bg-pass/10 text-pass" },
  FAIL: { icon: faCircleXmark, className: "bg-fail/10 text-fail" },
  NOT_DETERMINABLE: { icon: faTriangleExclamation, className: "bg-warn/10 text-warn" },
};

/** Shared badge for both the review-status family (pending/accepted/edited/
 * rejected) and the rule-verdict family (PASS/FAIL/NOT_DETERMINABLE) -- kept
 * as two visually distinct color groups per docs/context/06, never
 * conflated into one meaning. Plain function, safe to render from Server
 * Components (no hooks). */
export function StatusBadge({ value }: { value: BadgeValue }) {
  const { icon, className } = CONFIG[value];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide whitespace-nowrap ${className}`}
    >
      <FontAwesomeIcon icon={icon} className="h-3 w-3" />
      {value}
    </span>
  );
}
