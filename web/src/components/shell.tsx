"use client";

import { ButtonLink } from "@/components/base/buttons/button";
import { copy } from "@/content/copy";
import { cx } from "@/utils/cx";
import { RiFileList3Line, RiGuideLine, RiRouteLine, RiScales3Line } from "@remixicon/react";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const links = [
  { href: "/", label: copy.explorer, icon: RiRouteLine },
  { href: "/friction", label: copy.friction, icon: RiGuideLine },
  { href: "/proforma", label: copy.proforma, icon: RiFileList3Line },
  { href: "/scenarios", label: copy.scenarios, icon: RiScales3Line },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-background-full">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-5 lg:flex-row lg:px-6 lg:py-8">
        <aside className="flex flex-col gap-4 lg:w-56 lg:shrink-0">
          <div className="px-1">
            <p className="text-headline-semibold text-text-primary">{copy.brand}</p>
            <p className="text-caption-1-regular text-text-tertiary">{copy.brandNote}</p>
          </div>
          <nav className="flex flex-row flex-wrap gap-2 lg:flex-col" aria-label={copy.brand}>
            {links.map((link) => {
              const current = pathname === link.href;
              return (
                <ButtonLink
                  key={link.href}
                  href={link.href}
                  variant={current ? "primary" : "ghost"}
                  leadingIcon={link.icon}
                  aria-current={current ? "page" : undefined}
                  className={cx("justify-start", !current && "w-full")}
                >
                  {link.label}
                </ButtonLink>
              );
            })}
          </nav>
        </aside>
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </div>
  );
}
