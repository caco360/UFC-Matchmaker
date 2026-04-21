"use client";

import Link from "next/link";
import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { searchFighters } from "@/lib/api";
import type { FighterSearchResult } from "@/lib/types";


export function FighterSearch() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [results, setResults] = useState<FighterSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const normalized = deferredQuery.trim();
    if (!normalized) {
      setResults([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    searchFighters(normalized, controller.signal)
      .then((nextResults) => {
        startTransition(() => {
          setResults(nextResults);
        });
      })
      .catch((caughtError: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(caughtError.message || "Unable to load fighters right now.");
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [deferredQuery]);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6">
      <label className="block">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Type a UFC fighter name"
          className="w-full border border-charcoal/15 bg-white/85 px-6 py-5 text-center text-lg text-charcoal shadow-soft outline-none transition placeholder:text-ash/80 focus:border-ember sm:text-xl"
        />
      </label>

      <div className="mx-auto w-full max-w-2xl text-left">
        {isLoading ? (
          <p className="mb-4 text-xs uppercase tracking-[0.18em] text-ember">
            Loading
          </p>
        ) : null}

        {!query.trim() ? null : error ? (
          <p className="border border-ember/20 bg-ember/5 px-4 py-3 text-sm leading-6 text-ember">
            {error}
          </p>
        ) : !isLoading && results.length === 0 ? (
          <p className="text-sm leading-7 text-charcoal/70">
            No fighter matched that search.
          </p>
        ) : null}

        <div className="divide-y divide-charcoal/10 bg-white/55">
          {results.map((fighter) => (
            <Link
              key={fighter.slug}
              href={`/fighters/${fighter.slug}`}
              className="group flex items-end justify-between gap-6 px-4 py-5 transition hover:translate-x-1"
            >
              <div className="space-y-1">
                <p className="font-display text-2xl font-medium text-charcoal transition group-hover:text-ember">
                  {fighter.fighter_name}
                </p>
                <p className="text-sm uppercase tracking-[0.16em] text-ash">
                  {fighter.weight_class}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-charcoal/80">
                  Rank #{fighter.fighter_rank_in_class}
                </p>
                <p className="text-xs uppercase tracking-[0.16em] text-ash">
                  {fighter.last_result_bucket}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
