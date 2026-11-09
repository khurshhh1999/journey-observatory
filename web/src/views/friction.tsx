"use client";

import { Chip } from "@/components/base/badges/chip";
import { Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from "@/components/base/table/table";
import { copy } from "@/content/copy";
import friction from "@/data/friction.json";
import { formatCount, formatPercent } from "@/lib/format";
import { useState } from "react";
import { CaseDrawer, Notices, type JourneyCase } from "./parts";

type VariantRow = {
  id: string;
  label: string;
  rank: number;
  cases: number;
  dropoffCases: number;
  dropoffRate: number;
  score: number;
  contacts: number;
  high: boolean;
  evidence: JourneyCase[];
};

const rows = friction.variants as VariantRow[];

export function FrictionView() {
  const [selected, setSelected] = useState<string | null>(rows.find((row) => row.high)?.id ?? null);
  const [caseId, setCaseId] = useState<string | null>(null);
  const current = rows.find((row) => row.id === selected) ?? null;
  const open = current?.evidence.find((item) => item.id === caseId) ?? null;

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <h1 className="text-title-2-semibold text-text-primary">{copy.frictionTitle}</h1>
        <p className="max-w-2xl text-body-regular text-text-secondary">{copy.frictionDescription}</p>
      </header>
      <Notices />
      <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
        <Table
          aria-label={copy.frictionTable}
          size="sm"
          selectionMode="single"
          selectedKeys={selected ? [selected] : []}
          onSelectionChange={(keys) => {
            if (keys === "all") return;
            const id = [...keys][0];
            setSelected(id ? String(id) : null);
            setCaseId(null);
          }}
        >
          <TableHeader>
            <TableColumn isRowHeader>{copy.variant}</TableColumn>
            <TableColumn>{copy.volume}</TableColumn>
            <TableColumn>{copy.dropoff}</TableColumn>
            <TableColumn>{copy.rank}</TableColumn>
          </TableHeader>
          <TableBody items={rows}>
            {(item) => (
              <TableRow id={item.id}>
                <TableCell>
                  <span className="flex items-center gap-2">
                    <span>{item.label}</span>
                    {item.high ? <Chip color="orange" variant="caption">{copy.highGroup}</Chip> : null}
                  </span>
                </TableCell>
                <TableCell>{formatCount(item.cases)}</TableCell>
                <TableCell>
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-1.5 w-16 overflow-hidden rounded-full bg-background-tertiary-default">
                      <span className="block h-full bg-chart-1" style={{ width: `${Math.round(item.dropoffRate * 100)}%` }} />
                    </span>
                    {formatPercent(item.dropoffRate)}
                  </span>
                </TableCell>
                <TableCell>{formatCount(item.rank)}</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <section className="flex flex-col gap-3">
        <h2 className="text-headline-semibold text-text-primary">{copy.evidence}</h2>
        {current && current.evidence.length > 0 ? (
          <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
            <Table
              aria-label={copy.evidence}
              size="sm"
              selectionMode="single"
              selectedKeys={caseId ? [caseId] : []}
              onSelectionChange={(keys) => {
                if (keys === "all") return;
                const id = [...keys][0];
                setCaseId(id ? String(id) : null);
              }}
            >
              <TableHeader>
                <TableColumn isRowHeader>{copy.reservation}</TableColumn>
                <TableColumn>{copy.property}</TableColumn>
                <TableColumn>{copy.outcome}</TableColumn>
              </TableHeader>
              <TableBody items={current.evidence}>
                {(item) => (
                  <TableRow id={item.id}>
                    <TableCell>{item.id}</TableCell>
                    <TableCell>{item.propertyName}</TableCell>
                    <TableCell>{item.outcomeLabel}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-body-regular text-text-secondary">
            {current ? copy.evidenceLimited : copy.selectVariant}
          </p>
        )}
      </section>
      <CaseDrawer item={open} open={caseId !== null} onOpenChange={(next) => { if (!next) setCaseId(null); }} />
    </div>
  );
}
