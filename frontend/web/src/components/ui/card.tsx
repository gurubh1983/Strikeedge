import * as React from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded border border-slate-800 bg-slate-900 p-4", className)} {...props} />;
}
