export type Workspace = {
  id: string;
  name: string;
  savedViews: Array<{ id: string; title: string }>;
};

const STORAGE_KEY = "strikeedge-workspaces";

export function loadWorkspaces(): Workspace[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  return JSON.parse(raw) as Workspace[];
}

export function saveWorkspaces(workspaces: Workspace[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspaces));
}
