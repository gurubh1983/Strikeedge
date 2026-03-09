"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthActor } from "@/hooks/use-auth-actor";
import { addWatchlistItem, createFavorite, createWatchlist, deleteFavorite, listFavorites, listWatchlists, type FavoritePayload, type WatchlistPayload } from "@/lib/api/client";

export default function PortfolioPage() {
  const { userId, isLoaded } = useAuthActor();
  const effectiveUserId = userId ?? "user-1";
  const [watchlistName, setWatchlistName] = useState("Core Watchlist");
  const [watchlistToken, setWatchlistToken] = useState("NIFTY_24000_CE");
  const [favoriteToken, setFavoriteToken] = useState("NIFTY_24000_CE");
  const [watchlists, setWatchlists] = useState<WatchlistPayload[]>([]);
  const [favorites, setFavorites] = useState<FavoritePayload[]>([]);

  const refreshAll = useCallback(async () => {
    const [w, f] = await Promise.all([listWatchlists(effectiveUserId), listFavorites(effectiveUserId)]);
    setWatchlists(w);
    setFavorites(f);
  }, [effectiveUserId]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    const wsBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace("http", "ws");
    const ws = new WebSocket(`${wsBase}/api/v1/ws/watchlists/${encodeURIComponent(effectiveUserId)}`);
    ws.onmessage = () => {
      void refreshAll();
    };
    return () => ws.close();
  }, [effectiveUserId, refreshAll]);

  async function createWatchlistAction() {
    await createWatchlist(effectiveUserId, watchlistName);
    await refreshAll();
  }

  async function addItemAction() {
    if (watchlists.length === 0) return;
    await addWatchlistItem(watchlists[0].id, watchlistToken);
    await refreshAll();
  }

  async function addFavoriteAction() {
    await createFavorite(effectiveUserId, favoriteToken);
    await refreshAll();
  }

  async function deleteFavoriteAction(token: string) {
    await deleteFavorite(effectiveUserId, token);
    await refreshAll();
  }

  if (!isLoaded) {
    return (
      <section className="space-y-4">
        <Card>
          <p className="text-sm text-slate-400">Loading...</p>
        </Card>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <Card>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Portfolio: Watchlists & Favorites</h2>
        {userId && (
          <p className="mb-2 text-xs text-slate-500">Signed in as {userId}</p>
        )}
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          <Input value={watchlistName} onChange={(e) => setWatchlistName(e.target.value)} placeholder="Watchlist name" />
          <Button onClick={() => void createWatchlistAction()}>Create Watchlist</Button>
          <Input value={watchlistToken} onChange={(e) => setWatchlistToken(e.target.value)} placeholder="Token for watchlist" />
          <Button onClick={() => void addItemAction()} variant="outline">
            Add to first watchlist
          </Button>
          <Button onClick={() => void refreshAll()} variant="outline">
            Refresh
          </Button>
        </div>
        <div className="mt-3 flex gap-2">
          <Input value={favoriteToken} onChange={(e) => setFavoriteToken(e.target.value)} placeholder="Favorite token" />
          <Button onClick={() => void addFavoriteAction()}>Add Favorite</Button>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-100">Watchlists</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-300">
          {watchlists.map((w) => (
            <li key={w.id} className="rounded border border-slate-800 p-2">
              <p className="font-medium text-slate-200">{w.name}</p>
              <p className="text-xs text-slate-400">{w.tokens.join(", ") || "No tokens yet"}</p>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-100">Favorites</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-300">
          {favorites.map((f) => (
            <li key={f.id} className="flex items-center justify-between rounded border border-slate-800 p-2">
              <span>{f.token}</span>
              <Button size="sm" variant="outline" onClick={() => void deleteFavoriteAction(f.token)}>
                Remove
              </Button>
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}
