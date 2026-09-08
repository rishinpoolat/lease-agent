import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "@/components/StatusBadge";

describe("StatusBadge", () => {
  it.each(["pending", "accepted", "edited", "rejected"] as const)(
    "renders the %s review status",
    (status) => {
      render(<StatusBadge value={status} />);
      expect(screen.getByText(status)).toBeInTheDocument();
    },
  );

  it.each(["PASS", "FAIL", "NOT_DETERMINABLE"] as const)("renders the %s rule verdict", (verdict) => {
    render(<StatusBadge value={verdict} />);
    expect(screen.getByText(verdict)).toBeInTheDocument();
  });
});
