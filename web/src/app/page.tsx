import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import { copy } from "@/content/copy";
import { ExplorerView } from "@/views/explorer";

export const metadata: Metadata = {
  title: copy.explorerTitle,
  description: copy.explorerDescription,
};

export default function Page() {
  return (
    <Shell>
      <ExplorerView />
    </Shell>
  );
}
