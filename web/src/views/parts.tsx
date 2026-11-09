"use client";

import { Chip } from "@/components/base/badges/chip";
import { Drawer, DrawerBody, DrawerHeader } from "@/components/base/drawer/drawer";
import { copy } from "@/content/copy";
import { formatUsd, formatWhen } from "@/lib/format";

export type JourneyEvent = {
  type: string;
  label: string;
  time: string;
  seq: number;
  amountCents: number;
  late: boolean;
  duplicate: boolean;
};

export type JourneyCase = {
  id: string;
  reservationId: number;
  propertyId: number;
  propertyName: string;
  market: string;
  variant: string;
  variantLabel: string;
  outcome: string;
  outcomeLabel: string;
  bookingValueCents: number;
  nights: number;
  folioPosts: number;
  charges: number;
  events: JourneyEvent[];
};

export function Notices({ modeled = false, simulated = false }: { modeled?: boolean; simulated?: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="rounded-2xl border border-border-button-default bg-background-secondary-default px-4 py-3 text-body-regular text-text-secondary">
        {copy.syntheticNotice}
      </p>
      {modeled ? (
        <p className="rounded-2xl border border-border-button-default bg-background-secondary-default px-4 py-3 text-body-regular text-text-secondary">
          {copy.modeledNotice}
        </p>
      ) : null}
      {simulated ? (
        <p className="rounded-2xl border border-border-button-default bg-background-secondary-default px-4 py-3 text-body-regular text-text-secondary">
          {copy.simulatedNotice}
        </p>
      ) : null}
    </div>
  );
}

export function CaseDrawer({
  item,
  open,
  onOpenChange,
}: {
  item: JourneyCase | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Drawer isOpen={open} onOpenChange={onOpenChange} size="lg" aria-label={copy.caseDetail}>
      <DrawerHeader
        title={item?.id ?? copy.caseDetail}
        description={item ? `${item.propertyName} · ${item.variantLabel}` : undefined}
      />
      <DrawerBody>
        {item ? (
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Chip color="neutral" variant="subtle">{item.outcomeLabel}</Chip>
              <Chip color="blue" variant="subtle">{formatUsd(item.bookingValueCents)}</Chip>
            </div>
            <dl className="grid grid-cols-2 gap-3">
              <div>
                <dt className="text-caption-1-regular text-text-tertiary">{copy.folioPosts}</dt>
                <dd className="text-body-medium text-text-primary">{item.folioPosts}</dd>
              </div>
              <div>
                <dt className="text-caption-1-regular text-text-tertiary">{copy.charges}</dt>
                <dd className="text-body-medium text-text-primary">{item.charges}</dd>
              </div>
            </dl>
            <ol className="flex flex-col">
              {item.events.map((event) => (
                <li key={`${event.seq}-${event.type}-${event.duplicate ? "dup" : "one"}`} className="flex gap-3 border-b border-separator-border py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-body-medium text-text-primary">{event.label}</p>
                    <p className="text-caption-1-regular text-text-tertiary">{formatWhen(event.time)}</p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    {event.amountCents > 0 ? (
                      <span className="text-body-regular text-text-secondary">{formatUsd(event.amountCents)}</span>
                    ) : null}
                    {event.late ? <Chip color="orange" variant="caption">{copy.late}</Chip> : null}
                    {event.duplicate ? <Chip color="rose" variant="caption">{copy.duplicate}</Chip> : null}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </DrawerBody>
    </Drawer>
  );
}
