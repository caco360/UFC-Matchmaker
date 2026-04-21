export type FighterSearchResult = {
  slug: string;
  fighter_name: string;
  weight_class: string;
  fighter_rank_in_class: number;
  fighter_rating: number;
  last_result_bucket: string;
};

export type Fighter = FighterSearchResult;

export type Matchup = {
  slot_number: number;
  target_direction: string;
  opponent_slug: string;
  opponent_name: string;
  opponent_rating: number;
  opponent_rank_in_class: number;
};
