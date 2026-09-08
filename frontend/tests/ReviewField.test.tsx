import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

const reviewLeaseField = vi.fn().mockResolvedValue({});
vi.mock("@/lib/api", () => ({
  api: { reviewLeaseField: (...args: unknown[]) => reviewLeaseField(...args) },
}));

import { ReviewField } from "@/components/ReviewField";
import type { LeaseField } from "@/lib/types";

const field: LeaseField = {
  id: "f1",
  field_name: "rent_amount",
  value: 8500,
  confidence: "high",
  source_excerpt: "rent of QAR 8,500",
  review_status: "pending",
  edited_value: null,
};

describe("ReviewField", () => {
  beforeEach(() => {
    refresh.mockClear();
    reviewLeaseField.mockClear();
  });

  it("accepts a field via the API and refreshes the page", async () => {
    render(<ReviewField field={field} />);
    fireEvent.click(screen.getByText("Accept"));
    expect(reviewLeaseField).toHaveBeenCalledWith("f1", "accept");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });

  it("rejects a field via the API and refreshes the page", async () => {
    render(<ReviewField field={field} />);
    fireEvent.click(screen.getByText("Reject"));
    expect(reviewLeaseField).toHaveBeenCalledWith("f1", "reject");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });

  it("edits a field with the new value via the API and refreshes the page", async () => {
    render(<ReviewField field={field} />);
    fireEvent.click(screen.getByText("Edit"));
    const input = screen.getByDisplayValue("8500");
    fireEvent.change(input, { target: { value: "9000" } });
    fireEvent.click(screen.getByText("Save"));
    expect(reviewLeaseField).toHaveBeenCalledWith("f1", "edit", "9000");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });
});
