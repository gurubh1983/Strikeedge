"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthActor } from "@/hooks/use-auth-actor";
import { listNotificationOutbox, listNotificationPreferences, upsertNotificationPreference, type NotificationOutboxPayload, type NotificationPreferencePayload } from "@/lib/api/client";

export default function AlertsPage() {
  const { userId, isLoaded } = useAuthActor();
  const effectiveUserId = userId ?? "user-1";
  const [channel, setChannel] = useState<"email" | "push">("email");
  const [destination, setDestination] = useState("user@example.com");
  const [prefs, setPrefs] = useState<NotificationPreferencePayload[]>([]);
  const [outbox, setOutbox] = useState<NotificationOutboxPayload[]>([]);

  const refresh = useCallback(async () => {
    const [p, o] = await Promise.all([listNotificationPreferences(effectiveUserId), listNotificationOutbox(effectiveUserId)]);
    setPrefs(p);
    setOutbox(o);
  }, [effectiveUserId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function savePreference() {
    await upsertNotificationPreference({
      user_id: effectiveUserId,
      channel,
      destination,
      enabled: true
    });
    await refresh();
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
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Alerts & Notifications</h2>
        {userId && <p className="mb-2 text-xs text-slate-500">Signed in as {userId}</p>}
        <div className="grid grid-cols-1 gap-2 md:grid-cols-4">
          <select
            value={channel}
            onChange={(e) => setChannel(e.target.value as "email" | "push")}
            className="h-9 rounded border border-slate-700 bg-slate-950 px-3 text-sm text-slate-100"
          >
            <option value="email">email</option>
            <option value="push">push</option>
          </select>
          <Input value={destination} onChange={(e) => setDestination(e.target.value)} placeholder="Destination" />
          <div className="flex gap-2">
            <Button onClick={() => void savePreference()}>Save</Button>
            <Button variant="outline" onClick={() => void refresh()}>
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-100">Preferences</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-300">
          {prefs.map((p) => (
            <li key={p.id} className="rounded border border-slate-800 p-2">
              {p.channel}: {p.destination} ({p.enabled ? "enabled" : "disabled"})
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-100">Outbox</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-300">
          {outbox.map((o) => (
            <li key={o.id} className="rounded border border-slate-800 p-2">
              <p className="font-medium text-slate-200">
                {o.channel} {"->"} {o.destination}
              </p>
              <p className="text-xs text-slate-400">{o.subject}</p>
              <p className="text-xs text-indigo-300">{o.status}</p>
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}
