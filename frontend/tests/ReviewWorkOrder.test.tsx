import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

const reviewWorkOrder = vi.fn().mockResolvedValue({});
vi.mock("@/lib/api", () => ({
  api: { reviewWorkOrder: (...args: unknown[]) => reviewWorkOrder(...args) },
}));

import { ReviewWorkOrder } from "@/components/ReviewWorkOrder";
import type { WorkOrder } from "@/lib/types";

const workOrder: WorkOrder = {
  id: "wo1",
  title: "Replace AC filter",
  description: "Visible dust buildup on the unit",
  severity: "medium",
  review_status: "pending",
};

describe("ReviewWorkOrder", () => {
  beforeEach(() => {
    refresh.mockClear();
    reviewWorkOrder.mockClear();
  });

  it("accepts a work order via the API and refreshes the page", async () => {
    render(<ReviewWorkOrder workOrder={workOrder} />);
    fireEvent.click(screen.getByText("Accept"));
    expect(reviewWorkOrder).toHaveBeenCalledWith("wo1", "accept");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });

  it("rejects a work order via the API and refreshes the page", async () => {
    render(<ReviewWorkOrder workOrder={workOrder} />);
    fireEvent.click(screen.getByText("Reject"));
    expect(reviewWorkOrder).toHaveBeenCalledWith("wo1", "reject");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });
});
