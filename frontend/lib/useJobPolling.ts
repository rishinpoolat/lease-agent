"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import type { JobStatusResponse } from "./types";

const POLL_INTERVAL_MS = 1500;

/** Polls GET /jobs/{id} until status is done/failed. Simple interval poll is
 * enough at this scale -- see docs/context/05-pipeline-architecture.md. */
export function useJobPolling(jobId: string | null): JobStatusResponse | null {
  const [job, setJob] = useState<JobStatusResponse | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;

    async function poll() {
      try {
        const result = await api.getJob(jobId as string);
        if (cancelled) return;
        setJob(result);
        if (result.status !== "done" && result.status !== "failed") {
          setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch {
        if (!cancelled) setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  return job;
}
