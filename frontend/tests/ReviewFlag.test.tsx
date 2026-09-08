import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

const reviewFlag = vi.fn().mockResolvedValue({});
vi.mock("@/lib/api", () => ({
  api: { reviewFlag: (...args: unknown[]) => reviewFlag(...args) },
}));

import { ReviewFlag } from "@/components/ReviewFlag";
import type { Flag } from "@/lib/types";

const flag: Flag = {
  id: "fl1",
  field_name: "deposit_amount",
  description: "Deposit missing from the document",
  severity: "high",
  review_status: "pending",
};

describe("ReviewFlag", () => {
  beforeEach(() => {
    refresh.mockClear();
    reviewFlag.mockClear();
  });

  it("accepts a flag via the API and refreshes the page", async () => {
    render(<ReviewFlag flag={flag} />);
    fireEvent.click(screen.getByText("Accept"));
    expect(reviewFlag).toHaveBeenCalledWith("fl1", "accept");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });

  it("rejects a flag via the API and refreshes the page, without deleting it client-side", async () => {
    render(<ReviewFlag flag={flag} />);
    fireEvent.click(screen.getByText("Reject"));
    expect(reviewFlag).toHaveBeenCalledWith("fl1", "reject");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });
});
