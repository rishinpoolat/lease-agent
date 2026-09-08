"use client";

import { faCamera, faCheckCircle, faSpinner, faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Link from "next/link";
import { use, useState } from "react";

import { Button } from "@/components/ui/button";
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
      <h1 className="mb-1 text-xl font-semibold text-foreground">Report an issue — {unitId}</h1>
      <p className="mb-5 text-sm text-muted-foreground">
        Upload one or more photos of the unit. The agent assesses condition, identifies visible
        contents/equipment, and drafts a work order if anything needs attention.
      </p>

      {!jobId && (
        <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center shadow-sm">
          <FontAwesomeIcon icon={faCamera} className="mx-auto mb-3 h-8 w-8 text-primary" />
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="mx-auto block text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary/10 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-primary hover:file:bg-primary/20"
          />
          <div className="mt-4">
            <Button onClick={handleSubmit} disabled={files.length === 0} size="sm">
              Upload {files.length > 0 ? `(${files.length})` : ""}
            </Button>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-fail">
          <FontAwesomeIcon icon={faTriangleExclamation} className="h-3.5 w-3.5" />
          {error}
        </p>
      )}

      {jobId && (
        <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <p className="flex items-center gap-2 text-sm text-foreground">
            {job?.status !== "done" && job?.status !== "failed" && (
              <FontAwesomeIcon icon={faSpinner} className="h-3.5 w-3.5 animate-spin text-primary" />
            )}
            Job <code className="rounded bg-muted px-1 py-0.5">{jobId}</code>:{" "}
            <strong>{job?.status ?? "submitting..."}</strong>
          </p>
          {job?.status === "failed" && (
            <p className="mt-2 flex items-center gap-1.5 text-sm text-fail">
              <FontAwesomeIcon icon={faTriangleExclamation} className="h-3.5 w-3.5" />
              {job.error}
            </p>
          )}
          {job?.status === "done" && (
            <p className="mt-2 flex items-center gap-1.5 text-sm text-pass">
              <FontAwesomeIcon icon={faCheckCircle} className="h-3.5 w-3.5" />
              Done — back to{" "}
              <Link className="text-primary hover:underline" href={`/units/${unitId}`}>
                the unit page
              </Link>{" "}
              to review the assessment.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
