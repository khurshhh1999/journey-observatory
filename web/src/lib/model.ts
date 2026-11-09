export type Scales = {
  bookingRecoveryScale: number;
  contactRecoveryScale: number;
  marginScale: number;
  costScale: number;
};

export type Ratio = {
  n: number;
  d: number;
};

export type VariantInput = {
  id: string;
  label: string;
  cases: number;
  dropoffCases: number;
  contacts: number;
  dropoffValueCents: number;
  bookingRecovery: Ratio;
  contactRecovery: Ratio;
};

export type ScenarioInput = {
  windowDays: number;
  marginRate: Ratio;
  handlingMinutes: Ratio;
  costPerMinute: Ratio;
  variants: VariantInput[];
  presets: Record<string, Scales>;
  results: Record<string, ScenarioTotals>;
};

export type ScenarioTotals = {
  revenueCents: number;
  marginCents: number;
  supportCents: number;
  modeledCents: number;
  observedLossCents: number;
  contactReduction: number;
  avoidedContacts: number;
  workloadContacts: number;
};

type Rational = { n: number; d: number };

function gcd(left: number, right: number): number {
  let a = Math.abs(left);
  let b = Math.abs(right);
  while (b) {
    const next = a % b;
    a = b;
    b = next;
  }
  return a || 1;
}

function rational(numerator: number, denominator = 1): Rational {
  if (denominator < 0) {
    numerator = -numerator;
    denominator = -denominator;
  }
  const divisor = gcd(numerator, denominator);
  return { n: numerator / divisor, d: denominator / divisor };
}

function multiply(left: Rational, right: Rational): Rational {
  return rational(left.n * right.n, left.d * right.d);
}

function roundHalfUp(value: Rational): number {
  if (value.n >= 0) {
    return Math.floor((2 * value.n + value.d) / (2 * value.d));
  }
  return -Math.floor((2 * -value.n + value.d) / (2 * value.d));
}

function annualize(cents: number, windowDays: number): number {
  return roundHalfUp(rational(cents * 365, windowDays));
}

function scaleRatio(value: number): Rational {
  return rational(Math.round(value * 20), 20);
}

export function workingForecast(input: ScenarioInput, scales: Scales): ScenarioTotals {
  const bookingScale = scaleRatio(scales.bookingRecoveryScale);
  const contactScale = scaleRatio(scales.contactRecoveryScale);
  const marginRate = multiply(input.marginRate, scaleRatio(scales.marginScale));
  const minuteCents = multiply(
    multiply(multiply(input.handlingMinutes, input.costPerMinute), scaleRatio(scales.costScale)),
    rational(100),
  );
  let revenue = 0;
  let margin = 0;
  let support = 0;
  let avoided = 0;
  let workload = 0;
  for (const variant of input.variants) {
    const booking = multiply(variant.bookingRecovery, bookingScale);
    const contact = multiply(variant.contactRecovery, contactScale);
    const cappedBooking = booking.n > booking.d ? rational(1) : booking;
    const cappedContact = contact.n > contact.d ? rational(1) : contact;
    const recovered = roundHalfUp(multiply(rational(variant.dropoffValueCents), cappedBooking));
    const marginCents = roundHalfUp(multiply(rational(recovered), marginRate));
    const supportCents = roundHalfUp(multiply(multiply(rational(variant.contacts), cappedContact), minuteCents));
    revenue += annualize(recovered, input.windowDays);
    margin += annualize(marginCents, input.windowDays);
    support += annualize(supportCents, input.windowDays);
    avoided += (variant.contacts * cappedContact.n) / cappedContact.d;
    workload += variant.contacts;
  }
  const base = input.results.base;
  return {
    revenueCents: revenue,
    marginCents: margin,
    supportCents: support,
    modeledCents: margin + support,
    observedLossCents: base.observedLossCents,
    contactReduction: workload === 0 ? 0 : avoided / workload,
    avoidedContacts: avoided,
    workloadContacts: workload,
  };
}
