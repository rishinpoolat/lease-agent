import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

const acceptUnitMatch = vi.fn().mockResolvedValue({});
vi.mock("@/lib/api", () => ({
  api: { acceptUnitMatch: (...args: unknown[]) => acceptUnitMatch(...args) },
}));

import { AcceptUnitMatchCard } from "@/components/AcceptUnitMatchCard";

describe("AcceptUnitMatchCard", () => {
  beforeEach(() => {
    refresh.mockClear();
    acceptUnitMatch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("makes no API call when the confirmation dialog is declined", () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<AcceptUnitMatchCard leaseId="lease-1" unitLabel="Apartment 1204" />);
    fireEvent.click(screen.getByText("Accept unit match"));
    expect(acceptUnitMatch).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
  });

  it("accepts the unit match and refreshes the page once the developer confirms", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<AcceptUnitMatchCard leaseId="lease-1" unitLabel="Apartment 1204" />);
    fireEvent.click(screen.getByText("Accept unit match"));
    expect(acceptUnitMatch).toHaveBeenCalledWith("lease-1");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalledOnce());
  });
});
