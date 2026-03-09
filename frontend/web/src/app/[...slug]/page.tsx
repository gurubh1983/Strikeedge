type Props = {
  params: { slug: string[] };
};

export default function ModulePlaceholderPage({ params }: Props) {
  return (
    <section className="rounded border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100">{params.slug.join(" / ")}</h2>
      <p className="mt-2 text-sm text-slate-300">Module shell is ready. Primary build focus is the screener/scanner workflow in this phase.</p>
    </section>
  );
}
