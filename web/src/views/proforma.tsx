"use client";

import { Chip } from "@/components/base/badges/chip";
import { Select, SelectItem } from "@/components/base/select/select";
import { Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from "@/components/base/table/table";
import { copy } from "@/content/copy";
import proforma from "@/data/proforma.json";
import { formatUsd } from "@/lib/format";
import { useMemo, useState } from "react";
import { Notices } from "./parts";

type Line = {
  id: string;
  label: string;
  propertyId?: number;
  revenueCents: number;
  marginCents: number;
  supportCents: number;
  modeledCents: number;
  observedLossCents: number;
};

const portfolio = proforma.lines as Line[];
const slices = proforma.byProperty as Line[];

export function ProformaView() {
  const [property, setProperty] = useState("all");
  const lines = useMemo(() => {
    if (property === "all") return portfolio;
    return slices.filter((line) => String(line.propertyId) === property);
  }, [property]);
  const totals = lines.reduce(
    (sum, line) => ({
      revenueCents: sum.revenueCents + line.revenueCents,
      marginCents: sum.marginCents + line.marginCents,
      supportCents: sum.supportCents + line.supportCents,
      modeledCents: sum.modeledCents + line.modeledCents,
    }),
    { revenueCents: 0, marginCents: 0, supportCents: 0, modeledCents: 0 },
  );
  const shown = property === "all"
    ? {
        revenueCents: proforma.totals.revenueCents,
        marginCents: proforma.totals.marginCents,
        supportCents: proforma.totals.supportCents,
        modeledCents: proforma.totals.modeledCents,
      }
    : totals;

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-title-2-semibold text-text-primary">{copy.proformaTitle}</h1>
          <Chip color="cyan" variant="subtle">{copy.modeled}</Chip>
        </div>
        <p className="max-w-2xl text-body-regular text-text-secondary">{copy.proformaDescription}</p>
      </header>
      <Notices modeled />
      <p className="max-w-2xl text-body-regular text-text-secondary">{copy.separateLines}</p>
      <Select
        aria-label={copy.property}
        label={copy.property}
        selectedKey={property}
        onSelectionChange={(key) => setProperty(String(key))}
        className="sm:w-56"
      >
        <SelectItem id="all">{copy.allProperties}</SelectItem>
        {proforma.properties.map((item) => (
          <SelectItem key={item.id} id={String(item.id)}>{item.name}</SelectItem>
        ))}
      </Select>
      <MoneyTable lines={lines} totals={shown} />
      <section className="flex flex-col gap-3">
        <h2 className="text-headline-semibold text-text-primary">{copy.rangeTitle}</h2>
        <p className="max-w-2xl text-body-regular text-text-secondary">{copy.portfolioScope}</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <RangeCard label={copy.downside} cents={proforma.range.low.modeledCents} />
          <RangeCard label={copy.base} cents={proforma.range.base.modeledCents} />
          <RangeCard label={copy.upside} cents={proforma.range.high.modeledCents} />
        </div>
      </section>
      <section className="flex flex-col gap-3">
        <h2 className="text-headline-semibold text-text-primary">{copy.sensitivity}</h2>
        <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
          <Table aria-label={copy.sensitivity} size="sm">
            <TableHeader>
              <TableColumn isRowHeader>{copy.assumption}</TableColumn>
              <TableColumn>{copy.low}</TableColumn>
              <TableColumn>{copy.base}</TableColumn>
              <TableColumn>{copy.high}</TableColumn>
            </TableHeader>
            <TableBody items={proforma.sensitivity}>
              {(item) => (
                <TableRow id={item.assumption}>
                  <TableCell>{item.assumption}</TableCell>
                  <TableCell>{formatUsd(item.low_cents)}</TableCell>
                  <TableCell>{formatUsd(item.base_cents)}</TableCell>
                  <TableCell>{formatUsd(item.high_cents)}</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}

function MoneyTable({ lines, totals }: { lines: Line[]; totals: { revenueCents: number; marginCents: number; supportCents: number; modeledCents: number } }) {
  const withTotal = [
    ...lines,
    {
      id: "total",
      label: copy.modeledTotal,
      revenueCents: totals.revenueCents,
      marginCents: totals.marginCents,
      supportCents: totals.supportCents,
      modeledCents: totals.modeledCents,
    },
  ];
  return (
    <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
      <Table aria-label={copy.proformaTitle} size="sm">
        <TableHeader>
          <TableColumn isRowHeader>{copy.variant}</TableColumn>
          <TableColumn>{copy.gross}</TableColumn>
          <TableColumn>{copy.margin}</TableColumn>
          <TableColumn>{copy.support}</TableColumn>
          <TableColumn>{copy.modeledTotal}</TableColumn>
        </TableHeader>
        <TableBody items={withTotal}>
          {(item) => (
            <TableRow id={item.id}>
              <TableCell>{item.label}</TableCell>
              <TableCell>{formatUsd(item.revenueCents)}</TableCell>
              <TableCell>{formatUsd(item.marginCents)}</TableCell>
              <TableCell>{formatUsd(item.supportCents)}</TableCell>
              <TableCell>{formatUsd(item.modeledCents)}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function RangeCard({ label, cents }: { label: string; cents: number }) {
  return (
    <section className="rounded-3xl border border-border-button-default bg-background-primary-default p-4">
      <p className="text-caption-1-semibold text-text-tertiary">{label}</p>
      <p className="mt-2 text-title-3-semibold text-text-primary">{formatUsd(cents)}</p>
    </section>
  );
}
