import { FighterSearch } from "@/components/fighter-search";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10 sm:px-10 lg:px-14">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col items-center justify-center">
        <section className="w-full space-y-10 text-center">
          <div className="space-y-5">
            <h1 className="font-display text-6xl font-medium leading-[0.92] text-charcoal sm:text-7xl lg:text-8xl">
              UFC Matchmaker
            </h1>
            <p className="mx-auto max-w-2xl text-base leading-7 text-ash sm:text-lg">
              Search a fighter and find their most logical future matchups.
            </p>
          </div>

          <FighterSearch />
        </section>
      </div>
    </main>
  );
}
