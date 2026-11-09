import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import { copy } from "@/content/copy";
import { ScenariosView } from "@/views/scenarios";

export const metadata: Metadata = {
  title: copy.scenariosTitle,
  description: copy.scenariosDescription,
};

export default function Page() {
  return (
    <Shell>
      <ScenariosView />
    </Shell>
  );
}
