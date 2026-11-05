"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import type { ApiMenuItem } from "@/lib/apiTypes";
import { ASAP_ARRIVAL_MINUTES } from "@/lib/pickup";

/**
 * The two things a customer chooses before they can order: where they are
 * heading and when they will arrive. Both are sent to the API, which decides
 * what is actually possible — this provider only holds the intent.
 */

const STORAGE_KEY = "readyby.booking.v1";

/** How often a long-lived page re-checks whether the chosen arrival is still ahead. */
const CLOCK_TICK_MS = 30_000;

function subscribeToClock(onChange: () => void) {
  const timer = setInterval(onChange, CLOCK_TICK_MS);
  return () => clearInterval(timer);
}

/**
 * A coarse clock read as an external store: the value only changes once per
 * tick, so reading it during render stays pure while a page left open for an
 * hour still notices that a chosen arrival time has slipped into the past.
 */
function useClock() {
  const tick = useSyncExternalStore(
    subscribeToClock,
    () => Math.floor(Date.now() / CLOCK_TICK_MS),
    () => 0,
  );
  return tick * CLOCK_TICK_MS;
}

function useIsHydrated() {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export interface BookingLine {
  menuItemId: number;
  name: string;
  /** Snapshot for display only. The server recomputes every price. */
  price: number;
  quantity: number;
  art: string;
}

interface BookingState {
  destinationKey: string | null;
  destinationName: string | null;
  arrivalAt: number | null;
  cafeSlug: string | null;
  cafeName: string | null;
  lines: BookingLine[];
}

type Action =
  | { type: "hydrate"; state: BookingState }
  | { type: "setDestination"; key: string; name: string }
  | { type: "setArrival"; at: number }
  | { type: "setCafe"; slug: string; name: string }
  | { type: "addItem"; item: ApiMenuItem }
  | { type: "setQuantity"; menuItemId: number; quantity: number }
  | { type: "clearCart" }
  | { type: "clearAll" };

function emptyState(): BookingState {
  return {
    destinationKey: null,
    destinationName: null,
    arrivalAt: null,
    cafeSlug: null,
    cafeName: null,
    lines: [],
  };
}

function lineQuantity(lines: BookingLine[], menuItemId: number) {
  return lines.find((line) => line.menuItemId === menuItemId)?.quantity ?? 0;
}

function reducer(state: BookingState, action: Action): BookingState {
  switch (action.type) {
    case "hydrate":
      return action.state;

    case "setDestination":
      return {
        ...state,
        destinationKey: action.key,
        destinationName: action.name,
      };

    case "setArrival":
      return { ...state, arrivalAt: action.at };

    case "setCafe": {
      // Switching café replaces the cart: a basket never spans two kitchens.
      if (state.cafeSlug === action.slug) return state;
      return {
        ...state,
        cafeSlug: action.slug,
        cafeName: action.name,
        lines: [],
      };
    }

    case "addItem": {
      if (state.cafeSlug === null) return state;
      const existing = lineQuantity(state.lines, action.item.id);
      const lines =
        existing > 0
          ? state.lines.map((line) =>
              line.menuItemId === action.item.id
                ? { ...line, quantity: Math.min(line.quantity + 1, 20) }
                : line,
            )
          : [
              ...state.lines,
              {
                menuItemId: action.item.id,
                name: action.item.name,
                price: Number(action.item.price),
                quantity: 1,
                art: action.item.art,
              },
            ];
      return { ...state, lines };
    }

    case "setQuantity": {
      const lines =
        action.quantity <= 0
          ? state.lines.filter((line) => line.menuItemId !== action.menuItemId)
          : state.lines.map((line) =>
              line.menuItemId === action.menuItemId
                ? { ...line, quantity: Math.min(action.quantity, 20) }
                : line,
            );
      return { ...state, lines };
    }

    case "clearCart":
      return { ...state, cafeSlug: null, cafeName: null, lines: [] };

    case "clearAll":
      return emptyState();

    default:
      return state;
  }
}

interface BookingContextValue extends BookingState {
  hydrated: boolean;
  /** ISO-8601 arrival for the API, or null when nothing is chosen yet. */
  arrivalIso: string | null;
  /** True once the arrival time is close enough that it needs re-sending. */
  hasArrival: boolean;
  cartCount: number;
  /** Display-only estimate. The server's `subtotal` is the real figure. */
  cartEstimate: number;
  cartLines: BookingLine[];
  selectDestination: (key: string, name: string) => void;
  selectArrival: (at: number) => void;
  /** Picks the soonest bookable arrival, used when a destination is chosen. */
  selectSoonestArrival: () => void;
  selectCafe: (slug: string, name: string) => void;
  addItem: (item: ApiMenuItem) => void;
  incrementItem: (menuItemId: number) => void;
  decrementItem: (menuItemId: number) => void;
  setQuantity: (menuItemId: number, quantity: number) => void;
  itemQuantity: (menuItemId: number) => number;
  clearCart: () => void;
  reset: () => void;
}

const BookingContext = createContext<BookingContextValue | null>(null);

function readStored(): BookingState | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return { ...emptyState(), ...(JSON.parse(raw) as BookingState) };
  } catch {
    return null;
  }
}

export function BookingProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, emptyState);
  const hydrated = useIsHydrated();
  const now = useClock();

  useEffect(() => {
    const stored = readStored();
    if (stored) dispatch({ type: "hydrate", state: stored });
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Non-fatal: the basket survives in memory for this visit.
    }
  }, [state, hydrated]);

  const selectDestination = useCallback(
    (key: string, name: string) => dispatch({ type: "setDestination", key, name }),
    [],
  );
  const selectArrival = useCallback((at: number) => dispatch({ type: "setArrival", at }), []);
  const selectSoonestArrival = useCallback(
    () => dispatch({ type: "setArrival", at: Date.now() + ASAP_ARRIVAL_MINUTES * 60_000 }),
    [],
  );
  const selectCafe = useCallback(
    (slug: string, name: string) => dispatch({ type: "setCafe", slug, name }),
    [],
  );
  const addItem = useCallback((item: ApiMenuItem) => dispatch({ type: "addItem", item }), []);
  const setQuantity = useCallback(
    (menuItemId: number, quantity: number) =>
      dispatch({ type: "setQuantity", menuItemId, quantity }),
    [],
  );
  const incrementItem = useCallback(
    (menuItemId: number) => {
      const line = state.lines.find((entry) => entry.menuItemId === menuItemId);
      if (line) dispatch({ type: "setQuantity", menuItemId, quantity: line.quantity + 1 });
    },
    [state.lines],
  );
  const decrementItem = useCallback(
    (menuItemId: number) => {
      const line = state.lines.find((entry) => entry.menuItemId === menuItemId);
      if (line) dispatch({ type: "setQuantity", menuItemId, quantity: line.quantity - 1 });
    },
    [state.lines],
  );
  const itemQuantity = useCallback(
    (menuItemId: number) => lineQuantity(state.lines, menuItemId),
    [state.lines],
  );
  const clearCart = useCallback(() => dispatch({ type: "clearCart" }), []);
  const reset = useCallback(() => dispatch({ type: "clearAll" }), []);

  const cartCount = useMemo(
    () => state.lines.reduce((sum, line) => sum + line.quantity, 0),
    [state.lines],
  );
  const cartEstimate = useMemo(
    () =>
      Math.round(state.lines.reduce((sum, line) => sum + line.price * line.quantity, 0) * 100) /
      100,
    [state.lines],
  );

  const value = useMemo<BookingContextValue>(
    () => ({
      ...state,
      hydrated,
      arrivalIso: state.arrivalAt ? new Date(state.arrivalAt).toISOString() : null,
      hasArrival: state.arrivalAt !== null && state.arrivalAt > now,
      cartCount,
      cartEstimate,
      cartLines: state.lines,
      selectDestination,
      selectArrival,
      selectSoonestArrival,
      selectCafe,
      addItem,
      incrementItem,
      decrementItem,
      setQuantity,
      itemQuantity,
      clearCart,
      reset,
    }),
    [
      state,
      hydrated,
      now,
      cartCount,
      cartEstimate,
      selectDestination,
      selectArrival,
      selectSoonestArrival,
      selectCafe,
      addItem,
      incrementItem,
      decrementItem,
      setQuantity,
      itemQuantity,
      clearCart,
      reset,
    ],
  );

  return <BookingContext.Provider value={value}>{children}</BookingContext.Provider>;
}

export function useBooking() {
  const context = useContext(BookingContext);
  if (!context) {
    throw new Error("useBooking must be used inside <BookingProvider>");
  }
  return context;
}