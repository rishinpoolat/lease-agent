"use client";

import Link from "next/link";
import { useState } from "react";

import { api } from "@/lib/api";
import { useJobPolling } from "@/lib/useJobPolling";

export default function UploadLeasePage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const job = useJobPolling(jobId);

  async function handleSubmit() {
    if (!file) return;
    setError(null);
    try {
      const { job_id } = await api.uploadLease(file);
      setJobId(job_id);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div>
      <h1>Upload a lease</h1>
      <p style={{ color: "var(--muted)" }}>
        Text or PDF. Extraction, flagging, and rule validation happen asynchronously via the worker
        queue -- this page polls the job until it completes.
      </p>

      {!jobId && (
        <div className="card">
          <input type="file" accept=".txt,.pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <div style={{ marginTop: 12 }}>
            <button onClick={handleSubmit} disabled={!file}>
              Upload
            </button>
          </div>
        </div>
      )}

      {error && <p style={{ color: "var(--fail)" }}>{error}</p>}

      {jobId && (
        <div className="card">
          <p>
            Job <code>{jobId}</code>: <strong>{job?.status ?? "submitting..."}</strong>
          </p>
          {job?.status === "failed" && <p style={{ color: "var(--fail)" }}>{job.error}</p>}
          {job?.status === "done" && (
            <p>
              Done -- go to <Link className="unit-link" href="/">the units list</Link> to find the
              matched unit and review the extracted lease.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
