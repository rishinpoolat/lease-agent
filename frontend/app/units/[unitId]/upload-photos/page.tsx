"use client";

import Link from "next/link";
import { use, useState } from "react";

import { api } from "@/lib/api";
import { useJobPolling } from "@/lib/useJobPolling";

export default function UploadPhotosPage({ params }: { params: Promise<{ unitId: string }> }) {
  const { unitId } = use(params);
  const [files, setFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const job = useJobPolling(jobId);

  async function handleSubmit() {
    if (files.length === 0) return;
    setError(null);
    try {
      const { job_id } = await api.uploadPhotos(unitId, files);
      setJobId(job_id);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div>
      <h1>Report an issue -- {unitId}</h1>
      <p style={{ color: "var(--muted)" }}>
        Upload one or more photos of the unit. The agent assesses condition, identifies visible
        contents/equipment, and drafts a work order if anything needs attention.
      </p>

      {!jobId && (
        <div className="card">
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          <div style={{ marginTop: 12 }}>
            <button onClick={handleSubmit} disabled={files.length === 0}>
              Upload {files.length > 0 ? `(${files.length})` : ""}
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
              Done -- back to <Link className="unit-link" href={`/units/${unitId}`}>the unit page</Link>{" "}
              to review the assessment.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
