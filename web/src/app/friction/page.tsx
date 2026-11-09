import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import { copy } from "@/content/copy";
import { FrictionView } from "@/views/friction";

export const metadata: Metadata = {
  title: copy.frictionTitle,
  description: copy.frictionDescription,
};

export default function Page() {
  return (
    <Shell>
      <FrictionView />
    </Shell>
  );
}
