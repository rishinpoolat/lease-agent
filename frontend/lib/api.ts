import type {
  Flag,
  JobStatusResponse,
  Lease,
  LeaseField,
  UnitDetail,
  UnitSummary,
  UploadAccepted,
  WorkOrder,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ReviewAction = "accept" | "reject" | "edit";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listUnits: () => request<UnitSummary[]>("/units"),
  getUnit: (unitId: string) => request<UnitDetail>(`/units/${unitId}`),

  uploadLease: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadAccepted>("/leases", { method: "POST", body: form });
  },

  uploadPhotos: (unitId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return request<UploadAccepted>(`/units/${unitId}/photos`, { method: "POST", body: form });
  },

  getJob: (jobId: string) => request<JobStatusResponse>(`/jobs/${jobId}`),

  reviewLeaseField: (id: string, action: ReviewAction, editedValue?: unknown) =>
    request<LeaseField>(`/lease-fields/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ action, edited_value: editedValue ?? null }),
    }),

  reviewFlag: (id: string, action: "accept" | "reject") =>
    request<Flag>(`/flags/${id}/review`, { method: "POST", body: JSON.stringify({ action }) }),

  reviewWorkOrder: (id: string, action: "accept" | "reject") =>
    request<WorkOrder>(`/work-orders/${id}/review`, { method: "POST", body: JSON.stringify({ action }) }),

  acceptUnitMatch: (leaseId: string) =>
    request<Lease>(`/leases/${leaseId}/accept-unit-match`, { method: "POST" }),
};
