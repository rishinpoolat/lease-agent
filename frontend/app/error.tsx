"use client";

import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
      <FontAwesomeIcon icon={faTriangleExclamation} className="mt-0.5 h-4 w-4 shrink-0 text-fail" />
      <div>
        <p className="text-sm font-medium text-fail">Something went wrong loading this page.</p>
        <p className="mt-1 text-xs text-muted-foreground">{error.message}</p>
        <Button onClick={reset} size="sm" variant="outline" className="mt-3">
          Try again
        </Button>
      </div>
    </div>
  );
}
