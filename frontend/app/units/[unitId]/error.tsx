"use client";

import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Link from "next/link";
import { useEffect } from "react";

import { Button, buttonVariants } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
      <FontAwesomeIcon icon={faTriangleExclamation} className="mt-0.5 h-4 w-4 shrink-0 text-fail" />
      <div>
        <p className="text-sm font-medium text-fail">Couldn&apos;t load this unit.</p>
        <p className="mt-1 text-xs text-muted-foreground">{error.message}</p>
        <div className="mt-3 flex gap-2">
          <Button onClick={reset} size="sm" variant="outline">
            Try again
          </Button>
          <Link href="/" className={buttonVariants({ size: "sm", variant: "outline" })}>
            Back to units
          </Link>
        </div>
      </div>
    </div>
  );
}
