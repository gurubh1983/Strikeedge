"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { listMarketplace, publishMarketplace, type MarketplaceStrategyPayload } from "@/lib/api/client";

export default function StrategyPage() {
  const [title, setTitle] = useState("Momentum Breakout");
  const [ownerId, setOwnerId] = useState("user-1");
  const [strategyId, setStrategyId] = useState("strategy-1");
  const [description, setDescription] = useState("Breakout with momentum confirmation");
  const [tags, setTags] = useState("momentum,breakout");
  const [items, setItems] = useState<MarketplaceStrategyPayload[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      setItems(await listMarketplace(50));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load marketplace");
    }
  }

  async function publish() {
    try {
      setError(null);
      await publishMarketplace({
        strategy_id: strategyId,
        owner_id: ownerId,
        title,
        description,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publish failed");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section className="space-y-4">
      <Card>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Strategy Marketplace</h2>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <Input value={ownerId} onChange={(e) => setOwnerId(e.target.value)} placeholder="Owner ID" />
          <Input value={strategyId} onChange={(e) => setStrategyId(e.target.value)} placeholder="Strategy ID" />
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
          <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="Tags comma-separated" />
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" className="md:col-span-2" />
        </div>
        <div className="mt-3 flex gap-2">
          <Button onClick={() => void publish()}>Publish</Button>
          <Button variant="outline" onClick={() => void refresh()}>
            Refresh
          </Button>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-400">{error}</p> : null}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-100">Published Strategies</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-300">
          {items.map((item) => (
            <li key={item.id} className="rounded border border-slate-800 p-2">
              <p className="font-medium text-slate-200">{item.title}</p>
              <p className="text-xs text-slate-400">{item.description}</p>
              <p className="mt-1 text-xs text-indigo-300">Share: {item.share_code}</p>
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}
