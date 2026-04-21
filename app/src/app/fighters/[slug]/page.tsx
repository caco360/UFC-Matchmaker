import Link from "next/link";

import { FighterDetail } from "@/components/fighter-detail";

type FighterPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function FighterPage({ params }: FighterPageProps) {
  const { slug } = await params;

  return (
    <main className="min-h-screen px-6 py-8 sm:px-10 lg:px-14">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-center justify-between border-b border-charcoal/10 pb-5">
          <Link
            href="/"
            className="text-sm uppercase tracking-[0.22em] text-ash transition hover:text-ember"
          >
            Back to search
          </Link>
          <p className="text-xs uppercase tracking-[0.24em] text-ash">
            Fighter detail
          </p>
        </div>

        <FighterDetail slug={slug} />
      </div>
    </main>
  );
}
