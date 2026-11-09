"use client";

import { Chip } from "@/components/base/badges/chip";
import { Button } from "@/components/base/buttons/button";
import { Slider } from "@/components/base/slider/slider";
import { Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from "@/components/base/table/table";
import { Tab, TabList, TabPanel, Tabs } from "@/components/base/tabs/tabs";
import { copy } from "@/content/copy";
import scenarios from "@/data/scenarios.json";
import { formatCount, formatPercent, formatUsd } from "@/lib/format";
import { workingForecast, type Scales, type ScenarioInput, type ScenarioTotals } from "@/lib/model";
import { useMemo, useState } from "react";
import { Notices } from "./parts";

const input = scenarios as ScenarioInput;

const tabs = [
  { id: "base", label: copy.base },
  { id: "upside", label: copy.upside },
  { id: "downside", label: copy.downside },
];

export function ScenariosView() {
  const [tab, setTab] = useState("base");
  const preset = input.presets[tab];
  const [scales, setScales] = useState<Scales>(preset);
  const [edited, setEdited] = useState(false);

  const working = useMemo(() => (edited ? workingForecast(input, scales) : input.results[tab]), [edited, scales, tab]);
  const forecast = working.modeledCents;

  function choose(next: string) {
    setTab(next);
    setScales(input.presets[next]);
    setEdited(false);
  }

  function update(partial: Partial<Scales>) {
    setScales((current) => ({ ...current, ...partial }));
    setEdited(true);
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-title-2-semibold text-text-primary">{copy.scenariosTitle}</h1>
          <Chip color="cyan" variant="subtle">{copy.modeled}</Chip>
          <Chip color="purple" variant="subtle">{copy.simulated}</Chip>
        </div>
        <p className="max-w-2xl text-body-regular text-text-secondary">{copy.scenariosDescription}</p>
      </header>
      <Notices modeled simulated />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Figure label={copy.observed} help={copy.observedHelp} value={formatUsd(input.results.base.observedLossCents)} />
        <Figure label={copy.recoverable} help={copy.recoverableHelp} value={formatUsd(input.results.base.modeledCents)} />
        <Figure label={copy.forecast} help={copy.forecastHelp} value={formatUsd(forecast)} />
        <Figure label={copy.postLaunch} help={copy.postLaunchHelp} value={copy.noneOnFile} />
      </div>
      <Tabs selectedKey={tab} onSelectionChange={(key) => choose(String(key))}>
        <TabList>
          {tabs.map((item) => (
            <Tab key={item.id} id={item.id}>{item.label}</Tab>
          ))}
        </TabList>
        {tabs.map((item) => (
          <TabPanel key={item.id} id={item.id}>
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_18rem]">
              <div className="flex flex-col gap-4 rounded-3xl border border-border-button-default bg-background-primary-default p-4">
                <Slider label={copy.bookingRecovery} minValue={0.4} maxValue={1.8} step={0.05} value={scales.bookingRecoveryScale} onChange={(value) => update({ bookingRecoveryScale: value })} formatValue={(value) => value.toFixed(2)} />
                <Slider label={copy.contactRecovery} minValue={0.4} maxValue={1.8} step={0.05} value={scales.contactRecoveryScale} onChange={(value) => update({ contactRecoveryScale: value })} formatValue={(value) => value.toFixed(2)} />
                <Slider label={copy.marginRate} minValue={0.4} maxValue={1.8} step={0.05} value={scales.marginScale} onChange={(value) => update({ marginScale: value })} formatValue={(value) => value.toFixed(2)} />
                <Slider label={copy.supportCost} minValue={0.4} maxValue={1.8} step={0.05} value={scales.costScale} onChange={(value) => update({ costScale: value })} formatValue={(value) => value.toFixed(2)} />
                <Button variant="secondary" onClick={() => { setScales(input.presets[tab]); setEdited(false); }}>{copy.reset}</Button>
              </div>
              <ContactCard totals={working} />
            </div>
          </TabPanel>
        ))}
      </Tabs>
      <section className="flex flex-col gap-3">
        <h2 className="text-headline-semibold text-text-primary">{copy.comparison}</h2>
        <div className="rounded-3xl border border-border-button-default bg-background-primary-default">
          <Table aria-label={copy.comparison} size="sm">
            <TableHeader>
              <TableColumn isRowHeader>{copy.assumption}</TableColumn>
              <TableColumn>{copy.base}</TableColumn>
              <TableColumn>{copy.upside}</TableColumn>
              <TableColumn>{copy.downside}</TableColumn>
              <TableColumn>{copy.working}</TableColumn>
            </TableHeader>
            <TableBody>
              <TableRow id="modeled">
                <TableCell>{copy.modeledTotal}</TableCell>
                <TableCell>{formatUsd(input.results.base.modeledCents)}</TableCell>
                <TableCell>{formatUsd(input.results.upside.modeledCents)}</TableCell>
                <TableCell>{formatUsd(input.results.downside.modeledCents)}</TableCell>
                <TableCell>{formatUsd(forecast)}</TableCell>
              </TableRow>
              <TableRow id="contacts">
                <TableCell>{copy.reduction}</TableCell>
                <TableCell>{formatPercent(input.results.base.contactReduction)}</TableCell>
                <TableCell>{formatPercent(input.results.upside.contactReduction)}</TableCell>
                <TableCell>{formatPercent(input.results.downside.contactReduction)}</TableCell>
                <TableCell>{formatPercent(working.contactReduction)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}

function Figure({ label, help, value }: { label: string; help: string; value: string }) {
  return (
    <section className="rounded-3xl border border-border-button-default bg-background-primary-default p-4">
      <h2 className="text-caption-1-semibold text-text-tertiary">{label}</h2>
      <p className="mt-2 text-title-3-semibold text-text-primary">{value}</p>
      <p className="mt-2 text-body-2-regular text-text-secondary">{help}</p>
    </section>
  );
}

function ContactCard({ totals }: { totals: ScenarioTotals }) {
  return (
    <section className="flex flex-col gap-3 rounded-3xl border border-border-button-default bg-background-secondary-default p-4">
      <h2 className="text-headline-semibold text-text-primary">{copy.contactTitle}</h2>
      <div>
        <p className="text-caption-1-regular text-text-tertiary">{copy.workload}</p>
        <p className="text-title-3-semibold text-text-primary">{formatCount(totals.workloadContacts)}</p>
      </div>
      <div>
        <p className="text-caption-1-regular text-text-tertiary">{copy.avoided}</p>
        <p className="text-title-3-semibold text-text-primary">{formatCount(totals.avoidedContacts)}</p>
      </div>
      <div>
        <p className="text-caption-1-regular text-text-tertiary">{copy.reduction}</p>
        <p className="text-title-3-semibold text-text-primary">{formatPercent(totals.contactReduction)}</p>
      </div>
    </section>
  );
}
