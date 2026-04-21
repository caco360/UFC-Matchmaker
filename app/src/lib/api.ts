import type { Fighter, FighterSearchResult, Matchup } from "@/lib/types";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function readJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    signal,
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("That fighter was not found.");
    }
    throw new Error("The API request failed.");
  }

  return response.json() as Promise<T>;
}

export function searchFighters(
  query: string,
  signal?: AbortSignal,
): Promise<FighterSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  return readJson<FighterSearchResult[]>(
    `/fighters/search?${params.toString()}`,
    signal,
  );
}

export function getFighter(slug: string, signal?: AbortSignal): Promise<Fighter> {
  return readJson<Fighter>(`/fighters/${slug}`, signal);
}

export function getFighterMatchups(
  slug: string,
  signal?: AbortSignal,
): Promise<Matchup[]> {
  return readJson<Matchup[]>(`/fighters/${slug}/matchups`, signal);
}
