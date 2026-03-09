import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return <input className={cn("h-9 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100", className)} ref={ref} {...props} />;
});
Input.displayName = "Input";

export { Input };
