import Link from "next/link";

import type { Matchup } from "@/lib/types";


type MatchupTableProps = {
  matchups: Matchup[];
};

export function MatchupTable({ matchups }: MatchupTableProps) {
  if (matchups.length === 0) {
    return (
      <p className="text-sm leading-7 text-charcoal/70">
        No matchup suggestions are available for this fighter yet.
      </p>
    );
  }

  return (
    <div className="overflow-hidden bg-white/70 shadow-soft">
      <div className="grid grid-cols-[0.7fr_2fr_1fr_1fr] gap-4 border-b border-charcoal/10 px-5 py-4 text-xs uppercase tracking-[0.18em] text-ash">
        <span>Slot</span>
        <span>Opponent</span>
        <span>Direction</span>
        <span className="text-right">Rank</span>
      </div>

      <div className="divide-y divide-charcoal/10">
        {matchups.map((matchup) => (
          <div
            key={`${matchup.opponent_slug}-${matchup.slot_number}`}
            className="grid grid-cols-[0.7fr_2fr_1fr_1fr] gap-4 px-5 py-5 text-sm text-charcoal"
          >
            <span className="text-charcoal/70">{matchup.slot_number}</span>
            <div className="space-y-1">
              <Link
                href={`/fighters/${matchup.opponent_slug}`}
                className="font-display text-xl font-medium transition hover:text-ember"
              >
                {matchup.opponent_name}
              </Link>
              <p className="text-xs uppercase tracking-[0.16em] text-ash">
                Rating {matchup.opponent_rating.toFixed(1)}
              </p>
            </div>
            <span className="text-charcoal/70">{matchup.target_direction}</span>
            <span className="text-right text-charcoal/70">
              #{matchup.opponent_rank_in_class}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
