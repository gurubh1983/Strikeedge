"use client";

import { useAuth } from "@clerk/nextjs";

/**
 * Returns the current user ID for API calls (clerk_user_id).
 * Use as actorId / user_id when calling backend endpoints.
 * Returns undefined when not signed in or Clerk not yet loaded.
 */
export function useAuthActor(): {
  userId: string | undefined;
  isLoaded: boolean;
  isSignedIn: boolean;
  getToken: () => Promise<string | null>;
} {
  const { userId, isLoaded, isSignedIn, getToken } = useAuth();
  return {
    userId: userId ?? undefined,
    isLoaded: isLoaded ?? true,
    isSignedIn: isSignedIn ?? false,
    getToken: getToken ?? (async () => null),
  };
}
