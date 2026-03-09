import * as React from "react";

import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, ...props }, ref) => {
  return <select className={cn("h-9 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100", className)} ref={ref} {...props} />;
});
Select.displayName = "Select";

export { Select };
