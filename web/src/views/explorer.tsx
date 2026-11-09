"use client";

import { Pagination } from "@/components/base/pagination/pagination";
import { SearchField } from "@/components/base/search-field/search-field";
import { Select, SelectItem } from "@/components/base/select/select";
import { Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from "@/components/base/table/table";
import { copy } from "@/content/copy";
import explorer from "@/data/explorer.json";
import { formatUsd } from "@/lib/format";
import { useMemo, useState } from "react";
import { CaseDrawer, Notices, type JourneyCase } from "./parts";

const cases = explorer.cases as JourneyCase[];
const pageSize = 8;

const outcomes = [
  { id: "all", label: copy.allOutcomes },
  { id: "completed", label: "Completed" },
  { id: "friction", label: "Friction" },
  { id: "voluntary_exit", label: "Voluntary exit" },
  { id: "policy_block", label: "Policy block" },
  { id: "telemetry_gap", label: "Telemetry gap" },
  { id: "censored", label: "Censored" },
  { id: "other", label: "Other break" },
];

export function ExplorerView() {
  const [property, setProperty] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return cases.filter((item) => {
      if (property !== "all" && String(item.propertyId) !== property) return false;
      if (outcome !== "all" && item.outcome !== outcome) return false;
      if (needle && !item.id.toLowerCase().includes(needle) && !item.propertyName.toLowerCase().includes(needle)) return false;
      return true;
    });
  }, [outcome, property, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const current = Math.min(page, totalPages);
  const visible = filtered.slice((current - 1) * pageSize, current * pageSize);
  const open = cases.find((item) => item.id === selected) ?? null;

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <h1 className="text-title-2-semibold text-text-primary">{copy.explorerTitle}</h1>
        <p className="max-w-2xl text-body-regular text-text-secondary">{copy.explorerDescription}</p>
      </header>
      <Notices />
      <p className="text-body-regular text-text-tertiary">{copy.sampleNote}</p>
      <div className="flex flex-wrap items-end gap-3">
        <Select
          aria-label={copy.property}
          label={copy.property}
          selectedKey={property}
          onSelectionChange={(key) => {
            setProperty(String(key));
            setPage(1);
          }}
          className="sm:w-56"
        >
          <SelectItem id="all">{copy.allProperties}</SelectItem>
          {explorer.properties.map((item) => (
            <SelectItem key={item.id} id={String(item.id)}>{item.name}</SelectItem>
          ))}
        </Select>
        <Select
          aria-label={copy.outcome}
          label={copy.outcome}
          selectedKey={outcome}
          onSelectionChange={(key) => {
            setOutcome(String(key));
            setPage(1);
          }}
          className="sm:w-56"
        >
          {outcomes.map((item) => (
            <SelectItem key={item.id} id={item.id}>{item.label}</SelectItem>
          ))}
        </Select>
        <SearchField
          aria-label={copy.search}
          placeholder={copy.search}
          value={query}
          onChange={(value) => {
            setQuery(value);
            setPage(1);
          }}
          className="w-full sm:w-64"
        />
      </div>
      {visible.length === 0 ? (
        <p className="rounded-3xl border border-border-button-default bg-background-primary-default px-4 py-8 text-center text-body-regular text-text-secondary">
          {copy.noJourneys}
        </p>
      ) : (
        <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
          <Table
            aria-label={copy.journeyTable}
            size="sm"
            selectionMode="single"
            selectedKeys={selected ? [selected] : []}
            onSelectionChange={(keys) => {
              if (keys === "all") return;
              const id = [...keys][0];
              setSelected(id ? String(id) : null);
            }}
          >
            <TableHeader>
              <TableColumn isRowHeader>{copy.reservation}</TableColumn>
              <TableColumn>{copy.property}</TableColumn>
              <TableColumn>{copy.market}</TableColumn>
              <TableColumn>{copy.outcome}</TableColumn>
              <TableColumn>{copy.variant}</TableColumn>
              <TableColumn>{copy.value}</TableColumn>
            </TableHeader>
            <TableBody items={visible}>
              {(item) => (
                <TableRow id={item.id}>
                  <TableCell>{item.id}</TableCell>
                  <TableCell>{item.propertyName}</TableCell>
                  <TableCell>{item.market}</TableCell>
                  <TableCell>{item.outcomeLabel}</TableCell>
                  <TableCell>{item.variantLabel}</TableCell>
                  <TableCell>{formatUsd(item.bookingValueCents)}</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}
      {totalPages > 1 ? (
        <Pagination page={current} totalPages={totalPages} onChange={setPage} aria-label={copy.journeyTable} />
      ) : null}
      <CaseDrawer item={open} open={selected !== null} onOpenChange={(next) => { if (!next) setSelected(null); }} />
    </div>
  );
}
