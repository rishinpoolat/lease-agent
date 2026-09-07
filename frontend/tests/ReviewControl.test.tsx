import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReviewControl } from "@/components/ReviewControl";

describe("ReviewControl", () => {
  it("shows the current review status as a badge", () => {
    render(<ReviewControl status="pending" onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("calls onAccept when Accept is clicked", () => {
    const onAccept = vi.fn();
    render(<ReviewControl status="pending" onAccept={onAccept} onReject={vi.fn()} />);
    fireEvent.click(screen.getByText("Accept"));
    expect(onAccept).toHaveBeenCalledOnce();
  });

  it("calls onReject when Reject is clicked, and does not delete anything client-side", () => {
    const onReject = vi.fn();
    render(<ReviewControl status="pending" onAccept={vi.fn()} onReject={onReject} />);
    fireEvent.click(screen.getByText("Reject"));
    expect(onReject).toHaveBeenCalledOnce();
  });

  it("disables Accept once already accepted, and Reject once already rejected", () => {
    const { rerender } = render(<ReviewControl status="accepted" onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText("Accept")).toBeDisabled();

    rerender(<ReviewControl status="rejected" onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText("Reject")).toBeDisabled();
  });

  it("does not render an Edit button unless onEdit is provided", () => {
    render(<ReviewControl status="pending" onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.queryByText("Edit")).not.toBeInTheDocument();
  });

  it("switches to an editable input and calls onEdit with the new value on Save", () => {
    const onEdit = vi.fn();
    render(<ReviewControl status="pending" onAccept={vi.fn()} onReject={vi.fn()} onEdit={onEdit} currentValue="8500" />);

    fireEvent.click(screen.getByText("Edit"));
    const input = screen.getByDisplayValue("8500");
    fireEvent.change(input, { target: { value: "9000" } });
    fireEvent.click(screen.getByText("Save"));

    expect(onEdit).toHaveBeenCalledWith("9000");
  });
});
