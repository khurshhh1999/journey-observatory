# Case rules

A case is one reservation. The guest and the property are attributes of that case. A guest can have more than one stay, and those stays stay separate.

Events are ordered by sequence, then by business time, then by event id. Business time can show up late. A late time does not reorder the case.

An event that repeats the same sequence and the same amount is one event. The extra copy is counted, then dropped, so a charge is not booked twice.

Three endings are kept apart from friction.

A guest who cancels before arrival, without a payment failure, took a voluntary exit. A guest who never arrives did the same. Neither is a broken process.

A policy decline is a block. It is not a journey the hotel failed to finish.

A missing check-in on a stay that still checks out is a telemetry gap. The stay happened. The missing event is not a failure.

A stay that is still open when the extract ends is censored. It is not scored as a drop-off.

Friction is what remains: a payment that fails and is retried and still does not clear, a room that is not ready at check-in, a folio dispute, a modification loop, a duplicate charge, a refund that stays open, a hold that expires, a rate that changes after confirm, and a second tender that fails.

Variants are ranked by affected journeys times drop-off. The high-friction group is the set above the gap in that score. The group is found by the ranking. It is not a list pasted into the result.
