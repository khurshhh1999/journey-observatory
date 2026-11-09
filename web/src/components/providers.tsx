"use client";

import { DirectionProvider } from "@/components/foundations/direction/direction";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return <DirectionProvider locale="en-US">{children}</DirectionProvider>;
}
