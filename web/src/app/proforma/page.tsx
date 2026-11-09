import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import { copy } from "@/content/copy";
import { ProformaView } from "@/views/proforma";

export const metadata: Metadata = {
  title: copy.proformaTitle,
  description: copy.proformaDescription,
};

export default function Page() {
  return (
    <Shell>
      <ProformaView />
    </Shell>
  );
}
