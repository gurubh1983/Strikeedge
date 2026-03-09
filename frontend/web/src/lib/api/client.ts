export type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  actorId?: string;
  bearerToken?: string | null;
  idempotencyKey?: string;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    "content-type": "application/json",
  };
  if (options.actorId) headers["x-actor-id"] = options.actorId;
  if (options.bearerToken) headers["Authorization"] = `Bearer ${options.bearerToken}`;
  if (options.idempotencyKey) headers["x-idempotency-key"] = options.idempotencyKey;

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export type ScanRule = {
  field:
    | "rsi_14"
    | "ema_20"
    | "macd"
    | "macd_signal"
    | "iv"
    | "oi"
    | "pcr"
    | "delta"
    | "gamma"
    | "oi_change_pct"
    | "volume"
    | "moneyness"
    | "expiry_days";
  operator: ">" | "<" | ">=" | "<=" | "==" | "crosses_above" | "crosses_below";
  value: number;
};

export type ScanGroup = {
  logical_operator: "AND" | "OR";
  rules: ScanRule[];
};

export type TechnicalScanRule = {
  indicator: string;
  operator: ">" | "<" | ">=" | "<=" | "==";
  value: number;
};

export type TechnicalScanRequestPayload = {
  underlyings?: string[];
  expiry?: string;
  timeframe?: string;
  rules: TechnicalScanRule[];
  filter_config?: { groups: Array<{ logic: "AND" | "OR"; conditions: unknown[] }>; group_logic?: "AND" | "OR" };
  candle_days?: number;
  max_strikes_per_underlying?: number;
};

export type TechnicalScanResult = {
  symbol: string;
  underlying: string;
  strike_price: number | null;
  option_type: string | null;
  ltp: number | null;
  oi: number | null;
  expiry?: string | null;
  indicators: Record<string, number | null>;
};

export type TechnicalScanResponsePayload = {
  results: TechnicalScanResult[];
  count: number;
};

export async function runTechnicalScan(payload: TechnicalScanRequestPayload): Promise<TechnicalScanResponsePayload> {
  return apiRequest<TechnicalScanResponsePayload>("/api/v1/scanner/technical", { method: "POST", body: payload });
}

export type ScanRequestPayload = {
  timeframe: "1m" | "5m" | "15m";
  underlying?: string;
  limit?: number;
  rules?: ScanRule[];
  groups?: ScanGroup[];
};

export type ScanResult = {
  token: string;
  matched: boolean;
  reason: string;
};

export type ScanResponsePayload = {
  scan_id: string;
  created_at: string;
  results: ScanResult[];
};

export type ChartResponse = {
  token: string;
  timeframe: string;
  candles: Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }>;
};

export async function runScan(
  payload: ScanRequestPayload,
  options?: { actorId?: string; bearerToken?: string | null; alertUserId?: string }
): Promise<ScanResponsePayload> {
  const path = options?.alertUserId
    ? `/api/v1/scan?alert_user_id=${encodeURIComponent(options.alertUserId)}`
    : "/api/v1/scan";
  return apiRequest<ScanResponsePayload>(path, {
    method: "POST",
    body: payload,
    actorId: options?.actorId,
    bearerToken: options?.bearerToken,
  });
}

export async function fetchScanResults(scanId: string): Promise<{ scan_id: string; status: string; results: ScanResult[] }> {
  return apiRequest<{ scan_id: string; status: string; results: ScanResult[] }>(`/api/v1/scan/${scanId}/results`);
}

export async function fetchChart(
  token: string,
  timeframe: "1m" | "5m" | "15m" = "5m",
  limit = 200
): Promise<ChartResponse> {
  return apiRequest<ChartResponse>(
    `/api/v1/chart/${encodeURIComponent(token)}?timeframe=${timeframe}&limit=${limit}`
  );
}

export async function fetchInstruments(): Promise<Array<{ token: string }>> {
  return apiRequest<Array<{ token: string }>>("/api/v1/instruments");
}

export type ScreenerPayload = {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  underlying?: string | null;
  timeframe: "1m" | "5m" | "15m";
  groups: ScanGroup[];
  created_at: string;
};

export async function createScreener(payload: {
  user_id: string;
  name: string;
  description?: string;
  underlying?: string;
  timeframe: "1m" | "5m" | "15m";
  groups: ScanGroup[];
}): Promise<ScreenerPayload> {
  return apiRequest<ScreenerPayload>("/api/v1/screeners", { method: "POST", body: payload });
}

export async function listScreeners(userId: string): Promise<ScreenerPayload[]> {
  return apiRequest<ScreenerPayload[]>(`/api/v1/screeners?user_id=${encodeURIComponent(userId)}`);
}

export async function getScreener(screenerId: string): Promise<ScreenerPayload> {
  return apiRequest<ScreenerPayload>(`/api/v1/screeners/${encodeURIComponent(screenerId)}`);
}

export type UserProfilePayload = {
  id: string;
  clerk_user_id: string;
  email: string | null;
  display_name: string | null;
  created_at: string;
  updated_at: string;
};

export type UserPreferencesPayload = {
  id: string;
  clerk_user_id: string;
  default_timeframe: "1m" | "5m" | "15m";
  default_indicator: "rsi_14" | "ema_20" | "macd" | "macd_signal";
  theme: "dark" | "light";
  created_at: string;
  updated_at: string;
};

export async function getUserProfile(actorId: string): Promise<UserProfilePayload> {
  return apiRequest<UserProfilePayload>("/api/v1/api/user", { actorId });
}

export async function putUserProfile(
  actorId: string,
  payload: { email?: string | null; display_name?: string | null }
): Promise<UserProfilePayload> {
  return apiRequest<UserProfilePayload>("/api/v1/api/user", { method: "PUT", actorId, body: payload });
}

export async function getUserPreferences(actorId: string): Promise<UserPreferencesPayload> {
  return apiRequest<UserPreferencesPayload>("/api/v1/user/preferences", { actorId });
}

export async function putUserPreferences(
  actorId: string,
  payload: {
    default_timeframe: "1m" | "5m" | "15m";
    default_indicator: "rsi_14" | "ema_20" | "macd" | "macd_signal";
    theme: "dark" | "light";
  }
): Promise<UserPreferencesPayload> {
  return apiRequest<UserPreferencesPayload>("/api/v1/user/preferences", { method: "PUT", actorId, body: payload });
}

export type OptionsChainRowPayload = {
  underlying: string;
  expiry: string;
  strike_price: number;
  call_token: string | null;
  call_symbol: string | null;
  call_oi: number | null;
  call_iv: number | null;
  call_ltp: number | null;
  put_token: string | null;
  put_symbol: string | null;
  put_oi: number | null;
  put_iv: number | null;
  put_ltp: number | null;
  put_call_ratio: number | null;
  total_oi_change: number | null;
  lot_size: number;
  fetched_at: string;
};

export type OptionsChainMetricsPayload = {
  underlying: string;
  expiry: string;
  strikes: number;
  total_call_oi: number;
  total_put_oi: number;
  put_call_ratio: number | null;
  total_oi_change: number;
};

export type StrikeGreeksPayload = {
  underlying: string;
  expiry: string;
  symbol: string;
  token: string;
  option_type: string;
  strike_price: number;
  spot: number;
  time_to_expiry_years: number;
  risk_free_rate: number;
  volatility: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
  calculated_at: string;
};

export type OIHeatmapPointPayload = {
  strike_price: number;
  total_oi: number;
  total_oi_change: number;
  total_oi_change_pct: number;
  recorded_at: string;
};

export async function fetchExpiries(underlying: string): Promise<{ underlying: string; expiries: Array<{ date: string; iso: string; expiry: number }> }> {
  return apiRequest(`/api/v1/fyers/expiries/${encodeURIComponent(underlying)}`);
}

export async function fetchFyersStatus(): Promise<{ authenticated: boolean; has_token: boolean }> {
  return apiRequest<{ authenticated: boolean; has_token: boolean }>("/api/v1/fyers/status");
}

export type MarketOverviewHeatmapItem = {
  symbol: string;
  name: string;
  change_pct: number;
  ltp: number | null;
};

export type MomentumMetrics = {
  advance_count: number;
  decline_count: number;
  breadth_pct: number;
  avg_stock_change: number;
  avg_sector_change: number;
  strongest_sector: MarketOverviewHeatmapItem | null;
  weakest_sector: MarketOverviewHeatmapItem | null;
  market_context: "expansion" | "rotation" | "caution" | "contraction";
  context_label: string;
  context_hint: string;
  nifty50_change: number;
  bank_nifty_change: number;
};

export type MarketOverviewPayload = {
  data_source: "live" | "previous_close" | "fallback";
  stocks_heatmap: MarketOverviewHeatmapItem[];
  sector_heatmap: MarketOverviewHeatmapItem[];
  top_winners: MarketOverviewHeatmapItem[];
  top_losers: MarketOverviewHeatmapItem[];
  momentum_metrics?: MomentumMetrics;
};

export async function fetchMarketOverview(): Promise<MarketOverviewPayload> {
  // Use relative path so Next.js API route can proxy/fallback (avoids 404 when backend route not loaded)
  const url = typeof window !== "undefined" ? "/api/v1/dashboard/market-overview" : `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/dashboard/market-overview`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API request failed: ${res.status}`);
  return res.json() as Promise<MarketOverviewPayload>;
}

export async function fetchOptionsChain(params: {
  underlying: string;
  expiry: string;
  limit?: number;
  refresh?: boolean;
}): Promise<OptionsChainRowPayload[]> {
  const query = new URLSearchParams({
    underlying: params.underlying,
    expiry: params.expiry,
    limit: String(params.limit ?? 200),
    refresh: String(Boolean(params.refresh))
  });
  return apiRequest<OptionsChainRowPayload[]>(`/api/v1/options/chain?${query.toString()}`);
}

export async function fetchOptionsMetrics(underlying: string, expiry: string): Promise<OptionsChainMetricsPayload> {
  return apiRequest<OptionsChainMetricsPayload>(
    `/api/v1/options/metrics?underlying=${encodeURIComponent(underlying)}&expiry=${encodeURIComponent(expiry)}`
  );
}

export async function calculateOptionsGreeks(params: {
  underlying: string;
  expiry: string;
  spot: number;
  time_to_expiry_years: number;
  risk_free_rate?: number;
}): Promise<{ calculated: number }> {
  const query = new URLSearchParams({
    underlying: params.underlying,
    expiry: params.expiry,
    spot: String(params.spot),
    time_to_expiry_years: String(params.time_to_expiry_years),
    risk_free_rate: String(params.risk_free_rate ?? 0.06)
  });
  return apiRequest<{ calculated: number }>(`/api/v1/options/greeks/calculate?${query.toString()}`, { method: "POST" });
}

export async function fetchStrikeGreeks(symbol: string): Promise<StrikeGreeksPayload> {
  return apiRequest<StrikeGreeksPayload>(`/api/v1/strikes/${encodeURIComponent(symbol)}/vol/greeks`);
}

export async function fetchOIHeatmap(underlying: string, expiry: string, limit = 200): Promise<OIHeatmapPointPayload[]> {
  return apiRequest<OIHeatmapPointPayload[]>(
    `/api/v1/options/oi/heatmap?underlying=${encodeURIComponent(underlying)}&expiry=${encodeURIComponent(expiry)}&limit=${limit}`
  );
}

export async function fetchStrikeCandles(symbol: string, timeframe: "1m" | "5m" | "15m" = "1m", limit = 200): Promise<
  Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }>
> {
  return apiRequest<Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }>>(
    `/api/v1/strikes/${encodeURIComponent(symbol)}/candles?timeframe=${timeframe}&limit=${limit}`
  );
}

export type AiInsightPayload = {
  thesis: string;
  confidence: number;
  factors: Array<Record<string, unknown>>;
  risk_flags: string[];
  sources: Array<Record<string, unknown>>;
};

export type AiSentimentPayload = {
  symbol: string;
  sentiment: "bullish" | "bearish" | "neutral";
  score: number;
  summary: string;
};

export type PatternSignalPayload = {
  pattern: string;
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  description: string;
};

export type PatternPayload = {
  symbol: string;
  timeframe: string;
  signals: PatternSignalPayload[];
};

export async function fetchAiInsights(symbol: string): Promise<AiInsightPayload> {
  return apiRequest<AiInsightPayload>(`/api/v1/ai/insights/${symbol}`);
}

export async function fetchAiSentiment(symbol: string): Promise<AiSentimentPayload> {
  return apiRequest<AiSentimentPayload>(`/api/v1/ai/sentiment/${symbol}`);
}

export async function fetchAiPatterns(symbol: string, timeframe = "5m"): Promise<PatternPayload> {
  return apiRequest<PatternPayload>(`/api/v1/ai/patterns/${symbol}?timeframe=${encodeURIComponent(timeframe)}`);
}

export type MarketplacePublishPayload = {
  strategy_id: string;
  owner_id: string;
  title: string;
  description: string;
  tags: string[];
};

export type MarketplaceStrategyPayload = MarketplacePublishPayload & {
  id: string;
  share_code: string;
  created_at: string;
};

export async function publishMarketplace(payload: MarketplacePublishPayload): Promise<MarketplaceStrategyPayload> {
  return apiRequest<MarketplaceStrategyPayload>("/api/v1/marketplace/publish", { method: "POST", body: payload });
}

export async function listMarketplace(limit = 100): Promise<MarketplaceStrategyPayload[]> {
  return apiRequest<MarketplaceStrategyPayload[]>(`/api/v1/marketplace/strategies?limit=${limit}`);
}

export type WatchlistPayload = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  tokens: string[];
};

export async function createWatchlist(userId: string, name: string): Promise<WatchlistPayload> {
  return apiRequest<WatchlistPayload>("/api/v1/watchlists", { method: "POST", body: { user_id: userId, name } });
}

export async function listWatchlists(userId: string): Promise<WatchlistPayload[]> {
  return apiRequest<WatchlistPayload[]>(`/api/v1/watchlists?user_id=${encodeURIComponent(userId)}`);
}

export async function addWatchlistItem(watchlistId: string, token: string): Promise<WatchlistPayload> {
  return apiRequest<WatchlistPayload>(`/api/v1/watchlists/${watchlistId}/items`, { method: "POST", body: { token } });
}

export type FavoritePayload = {
  id: string;
  user_id: string;
  token: string;
  created_at: string;
};

export async function createFavorite(userId: string, token: string): Promise<FavoritePayload> {
  return apiRequest<FavoritePayload>("/api/v1/favorites", { method: "POST", body: { user_id: userId, token } });
}

export async function listFavorites(userId: string): Promise<FavoritePayload[]> {
  return apiRequest<FavoritePayload[]>(`/api/v1/favorites?user_id=${encodeURIComponent(userId)}`);
}

export async function deleteFavorite(userId: string, token: string): Promise<{ deleted: boolean }> {
  return apiRequest<{ deleted: boolean }>(`/api/v1/favorites?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`, {
    method: "DELETE"
  });
}

export type NotificationPreferencePayload = {
  id: string;
  user_id: string;
  channel: string;
  destination: string;
  enabled: boolean;
  created_at: string;
};

export type NotificationOutboxPayload = {
  id: string;
  user_id: string;
  channel: string;
  destination: string;
  subject: string;
  body: string;
  status: string;
  error_message: string | null;
  created_at: string;
  sent_at: string | null;
};

export async function upsertNotificationPreference(payload: {
  user_id: string;
  channel: "email" | "push";
  destination: string;
  enabled: boolean;
}): Promise<NotificationPreferencePayload> {
  return apiRequest<NotificationPreferencePayload>("/api/v1/notifications/preferences", { method: "POST", body: payload });
}

export async function listNotificationPreferences(userId: string): Promise<NotificationPreferencePayload[]> {
  return apiRequest<NotificationPreferencePayload[]>(`/api/v1/notifications/preferences?user_id=${encodeURIComponent(userId)}`);
}

export async function listNotificationOutbox(userId: string): Promise<NotificationOutboxPayload[]> {
  return apiRequest<NotificationOutboxPayload[]>(`/api/v1/notifications/outbox?user_id=${encodeURIComponent(userId)}`);
}
