import Link from "next/link";

export function EditorStatus({
  description,
  title,
}: {
  description: string;
  title: string;
}) {
  return (
    <main className="min-h-screen bg-[#f4efe7] px-4 py-6 text-[#1b1916] sm:px-6 sm:py-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center">
        <section className="w-full rounded-[12px] border border-[#d4c8b8] bg-[#fbf7f1] px-6 py-10 shadow-[0_20px_60px_rgba(54,42,23,0.08)] sm:px-8">
          <p className="text-[0.72rem] tracking-[0.24em] text-[#7c6d58] uppercase">
            Case file editor
          </p>
          <h1 className="mt-3 text-[1.75rem] font-medium tracking-[-0.03em] text-[#1b1916] sm:text-[2.2rem]">
            {title}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#554d43] sm:text-[0.96rem]">
            {description}
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex h-10 items-center rounded-[8px] border border-[#cbbbab] bg-[#f5eee4] px-4 text-sm text-[#26231f] transition-colors duration-150 hover:bg-[#ede3d6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4efe7]"
            >
              Back to library
            </Link>
          </div>
        </section>
      </section>
    </main>
  );
}
