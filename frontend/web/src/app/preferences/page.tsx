"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthActor } from "@/hooks/use-auth-actor";
import { getUserPreferences, getUserProfile, putUserPreferences, putUserProfile } from "@/lib/api/client";

export default function PreferencesPage() {
  const { userId, isLoaded } = useAuthActor();
  const effectiveUserId = userId ?? "user-1";
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [timeframe, setTimeframe] = useState<"1m" | "5m" | "15m">("5m");
  const [indicator, setIndicator] = useState<"rsi_14" | "ema_20" | "macd" | "macd_signal">("rsi_14");
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const loadPreferences = useCallback(async () => {
    const [profile, prefs] = await Promise.all([getUserProfile(effectiveUserId), getUserPreferences(effectiveUserId)]);
    setEmail(profile.email ?? "");
    setDisplayName(profile.display_name ?? "");
    setTimeframe(prefs.default_timeframe);
    setIndicator(prefs.default_indicator);
    setTheme(prefs.theme);
  }, [effectiveUserId]);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  async function savePreferences() {
    await Promise.all([
      putUserProfile(effectiveUserId, { email: email || null, display_name: displayName || null }),
      putUserPreferences(effectiveUserId, {
        default_timeframe: timeframe,
        default_indicator: indicator,
        theme,
      }),
    ]);
    await loadPreferences();
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
        <h2 className="mb-3 text-lg font-semibold text-slate-100">User Preferences</h2>
        {userId && <p className="mb-2 text-xs text-slate-500">Signed in as {userId}</p>}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Display name" />
          <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as "1m" | "5m" | "15m")}
            className="h-9 rounded border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100"
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
          </select>
          <select
            value={indicator}
            onChange={(e) => setIndicator(e.target.value as "rsi_14" | "ema_20" | "macd" | "macd_signal")}
            className="h-9 rounded border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100"
          >
            <option value="rsi_14">RSI 14</option>
            <option value="ema_20">EMA 20</option>
            <option value="macd">MACD</option>
            <option value="macd_signal">MACD Signal</option>
          </select>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as "dark" | "light")}
            className="h-9 rounded border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
        <div className="mt-4 flex gap-2">
          <Button onClick={() => void savePreferences()}>Save</Button>
          <Button variant="outline" onClick={() => void loadPreferences()}>
            Load
          </Button>
        </div>
      </Card>
    </section>
  );
}
