"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getFighter, getFighterMatchups } from "@/lib/api";
import type { Fighter, Matchup } from "@/lib/types";

import { MatchupTable } from "./matchup-table";


type FighterDetailProps = {
  slug: string;
};

export function FighterDetail({ slug }: FighterDetailProps) {
  const [fighter, setFighter] = useState<Fighter | null>(null);
  const [matchups, setMatchups] = useState<Matchup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    Promise.all([
      getFighter(slug, controller.signal),
      getFighterMatchups(slug, controller.signal),
    ])
      .then(([fighterResponse, matchupResponse]) => {
        setFighter(fighterResponse);
        setMatchups(matchupResponse);
      })
      .catch((caughtError: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(caughtError.message || "Unable to load this fighter.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [slug]);

  if (isLoading) {
    return (
      <div className="space-y-10">
        <div className="space-y-3">
          <div className="h-4 w-28 animate-pulse bg-charcoal/10" />
          <div className="h-16 w-full max-w-xl animate-pulse bg-charcoal/10" />
          <div className="h-6 w-full max-w-md animate-pulse bg-charcoal/10" />
        </div>
        <div className="h-72 animate-pulse bg-white/60 shadow-soft" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <p className="text-xs uppercase tracking-[0.24em] text-ash">
          Error state
        </p>
        <p className="max-w-xl border border-ember/20 bg-ember/5 px-5 py-4 text-sm leading-7 text-ember">
          {error}
        </p>
        <Link
          href="/"
          className="inline-flex border border-charcoal/15 px-4 py-3 text-sm uppercase tracking-[0.18em] text-charcoal transition hover:border-ember hover:text-ember"
        >
          Return to search
        </Link>
      </div>
    );
  }

  if (!fighter) {
    return (
      <div className="space-y-4">
        <p className="text-xs uppercase tracking-[0.24em] text-ash">
          Not found
        </p>
        <p className="text-sm leading-7 text-charcoal/75">
          That fighter could not be found in the current matchup dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-14">
      <section className="grid gap-10 border-b border-charcoal/10 pb-10 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4">
          <p className="text-xs uppercase tracking-[0.24em] text-ember">
            Fighter snapshot
          </p>
          <h1 className="font-display text-5xl font-medium leading-[0.98] text-charcoal sm:text-6xl">
            {fighter.fighter_name}
          </h1>
          <p className="text-base leading-7 text-charcoal/75 sm:text-lg">
            {fighter.weight_class} ranking context from the current matchmaking
            table.
          </p>
        </div>

        <div className="grid gap-4 border-t border-charcoal/10 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
          <Metric label="Division rank" value={`#${fighter.fighter_rank_in_class}`} />
          <Metric label="Current rating" value={fighter.fighter_rating.toFixed(1)} />
          <Metric
            label="Last result bucket"
            value={fighter.last_result_bucket}
            accent={fighter.last_result_bucket === "win"}
          />
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4 border-b border-charcoal/10 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-ash">
              Suggested matchups
            </p>
            <h2 className="font-display text-3xl font-medium text-charcoal">
              Ordered by your current slot logic
            </h2>
          </div>
          <p className="text-sm text-charcoal/65">{matchups.length} options</p>
        </div>
        <MatchupTable matchups={matchups} />
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-charcoal/10 py-3 last:border-b-0">
      <p className="text-xs uppercase tracking-[0.22em] text-ash">{label}</p>
      <p className={`text-lg font-medium ${accent ? "text-ember" : "text-charcoal"}`}>
        {value}
      </p>
    </div>
  );
}
