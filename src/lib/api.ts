/**
 * The single door to the ReadyBy API.
 *
 * Every screen goes through `apiFetch` so the token, the error envelope and the
 * base URL are handled in exactly one place. The frontend never talks to the
 * network directly.
 */

import type {
  ApiCafe,
  ApiErrorBody,
  ApiMenuItem,
  ApiOrder,
  ApiOrderStatus,
  ApiUser,
  AuthResponse,
  BoardSummary,
  CafeListResponse,
  CafeMenuResponse,
  DestinationListResponse,
  MerchantCafe,
  MerchantCafeInput,
  MerchantMenuInput,
  MerchantMenuResponse,
  MerchantPickupSlots,
  NextAction,
  OrderListResponse,
  OrderStatus,
  PickupQuote,
  ProfileUpdateInput,
  UserRole,
} from "@/lib/apiTypes";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "readyby.token";

/** A failure the UI can show verbatim, because the backend wrote it for us. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fieldErrors: Record<string, string[]>;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.fieldErrors = body.field_errors ?? {};
  }

  /** True when the user needs to sign in again before anything else works. */
  get isUnauthenticated() {
    return this.status === 401;
  }

  get isForbidden() {
    return this.status === 403;
  }

  get isNotFound() {
    return this.status === 404;
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Private-mode storage failures shouldn't break the session in memory.
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
  signal?: AbortSignal;
}

const FALLBACK_ERROR: ApiErrorBody = {
  code: "server_error",
  message: "Something went wrong. Please try again in a moment.",
  field_errors: {},
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}) {
  const { method = "GET", body, headers = {}, auth = true, signal } = options;
  const token = auth ? getToken() : null;

  const requestHeaders: Record<string, string> = { Accept: "application/json", ...headers };
  if (token) requestHeaders.Authorization = `Token ${token}`;
  if (body !== undefined) requestHeaders["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    // A fetch TypeError is thrown for both "nothing is listening" and "the
    // browser blocked the response as a CORS violation". From here they are
    // indistinguishable, so report the two causes and the exact origin the
    // browser used - that string is the one piece of information needed to fix
    // a CORS misconfiguration, and it is invisible everywhere else.
    const origin =
      typeof window === "undefined" ? "the server" : window.location.origin;
    throw new ApiError(0, {
      code: "network_error",
      message: `ReadyBy's API at ${API_BASE_URL} did not respond to a request from ${origin}. Either the Django API isn't running (start it with "npm run dev" from the project root), or ${origin} is not an origin the API accepts - check CORS_ALLOWED_ORIGINS in backend/.env.`,
      field_errors: {},
    });
  }

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const body: ApiErrorBody =
      payload && typeof payload === "object" && "code" in payload
        ? (payload as ApiErrorBody)
        : {
            ...FALLBACK_ERROR,
            code: String(response.status),
            message: FALLBACK_ERROR.message,
          };
    throw new ApiError(response.status, body);
  }

  return payload as T;
}

/* -------------------------------------------------------------------------- */
/*  Query helpers                                                             */
/* -------------------------------------------------------------------------- */

export function buildQuery(params: Record<string, string | number | null | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/* -------------------------------------------------------------------------- */
/*  Auth                                                                      */
/* -------------------------------------------------------------------------- */

export function login(email: string, password: string) {
  return apiFetch<AuthResponse>("/api/auth/login/", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

export function register(input: {
  email: string;
  first_name: string;
  last_name?: string;
  password: string;
  confirm_password: string;
  phone?: string;
}) {
  return apiFetch<AuthResponse>("/api/auth/register/", {
    method: "POST",
    body: input,
    auth: false,
  });
}

export function logout() {
  return apiFetch<void>("/api/auth/logout/", { method: "POST" });
}

export function fetchMe() {
  return apiFetch<ApiUser>("/api/auth/me/");
}

/**
 * Edits the signed-in account. Only the fields in `ProfileUpdateInput` are
 * accepted by the API, so a crafted payload cannot change role or status.
 */
export function updateMe(input: ProfileUpdateInput) {
  return apiFetch<ApiUser>("/api/auth/me/", { method: "PATCH", body: input });
}

/* -------------------------------------------------------------------------- */
/*  Catalogue                                                                 */
/* -------------------------------------------------------------------------- */

export function fetchDestinations(signal?: AbortSignal) {
  return apiFetch<DestinationListResponse>("/api/destinations/", {
    auth: false,
    signal,
  });
}

export function fetchCafes(
  params: { destination?: string | null; arrivalTime?: string | null },
  signal?: AbortSignal,
) {
  const query = buildQuery({
    destination: params.destination ?? undefined,
    arrival_time: params.arrivalTime ?? undefined,
  });
  return apiFetch<CafeListResponse>(`/api/cafes/${query}`, { auth: false, signal });
}

export function fetchCafe(
  slug: string,
  params: { destination?: string | null; arrivalTime?: string | null },
  signal?: AbortSignal,
) {
  const query = buildQuery({
    destination: params.destination ?? undefined,
    arrival_time: params.arrivalTime ?? undefined,
  });
  return apiFetch<ApiCafe>(`/api/cafes/${slug}/${query}`, { auth: false, signal });
}

export function fetchMenu(slug: string, signal?: AbortSignal) {
  return apiFetch<CafeMenuResponse>(`/api/cafes/${slug}/menu/`, {
    auth: false,
    signal,
  });
}

export function fetchPickupQuote(
  slug: string,
  input: {
    items: Array<{ menu_item: number; quantity: number }>;
    arrivalTime?: string | null;
  },
  signal?: AbortSignal,
) {
  return apiFetch<PickupQuote>(`/api/cafes/${slug}/quote/`, {
    method: "POST",
    auth: false,
    signal,
    body: {
      items: input.items,
      arrival_time: input.arrivalTime ?? null,
    },
  });
}

export type { ApiMenuItem };

/* -------------------------------------------------------------------------- */
/*  Orders                                                                    */
/* -------------------------------------------------------------------------- */

export interface CreateOrderInput {
  cafe: string;
  destination?: string | null;
  arrivalTime: string;
  items: Array<{ menu_item: number; quantity: number }>;
  notes?: string;
}

/**
 * Places an order. `idempotencyKey` is generated once per checkout attempt so a
 * double tap, a retry or a flaky connection cannot create two orders.
 */
export function createOrder(input: CreateOrderInput, idempotencyKey: string) {
  return apiFetch<ApiOrder>("/api/orders/new/", {
    method: "POST",
    body: {
      cafe: input.cafe,
      destination: input.destination ?? "",
      arrival_time: input.arrivalTime,
      items: input.items,
      notes: input.notes ?? "",
      idempotency_key: idempotencyKey,
    },
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function fetchMyOrders(signal?: AbortSignal) {
  return apiFetch<OrderListResponse>("/api/orders/", { signal });
}

export function fetchOrder(publicId: string, signal?: AbortSignal) {
  return apiFetch<ApiOrder>(`/api/orders/${publicId}/`, { signal });
}

export function fetchOrderStatus(publicId: string, signal?: AbortSignal) {
  return apiFetch<ApiOrderStatus>(`/api/orders/${publicId}/status/`, { signal });
}

export function cancelOrder(publicId: string, reason = "") {
  return apiFetch<ApiOrder>(`/api/orders/${publicId}/cancel/`, {
    method: "POST",
    body: { reason },
  });
}

/* -------------------------------------------------------------------------- */
/*  Merchant                                                                  */
/* -------------------------------------------------------------------------- */

export function fetchMyCafe() {
  return apiFetch<MerchantCafe>("/api/merchant/cafe/");
}

export function updateMyCafe(input: MerchantCafeInput) {
  return apiFetch<MerchantCafe>("/api/merchant/cafe/", {
    method: "PATCH",
    body: input,
  });
}

export function fetchMerchantMenu(signal?: AbortSignal) {
  return apiFetch<MerchantMenuResponse>("/api/merchant/menu/", { signal });
}

export function createMenuItem(input: MerchantMenuInput) {
  return apiFetch<ApiMenuItem>("/api/merchant/menu/create/", {
    method: "POST",
    body: input,
  });
}

export function updateMenuItem(itemId: number, input: Partial<MerchantMenuInput>) {
  return apiFetch<ApiMenuItem>(`/api/merchant/menu/${itemId}/`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteMenuItem(itemId: number) {
  return apiFetch<void>(`/api/merchant/menu/${itemId}/`, {
    method: "DELETE",
  });
}

export function fetchMerchantPickupSlots(signal?: AbortSignal) {
  return apiFetch<MerchantPickupSlots>("/api/merchant/pickup-slots/", { signal });
}

export function fetchMerchantOrders(status?: OrderStatus, signal?: AbortSignal) {
  const query = buildQuery({ status });
  return apiFetch<OrderListResponse>(`/api/merchant/orders/${query}`, { signal });
}

export function fetchBoardSummary(signal?: AbortSignal) {
  return apiFetch<BoardSummary>("/api/merchant/orders/summary/", { signal });
}

export function updateOrderStatus(publicId: string, status: OrderStatus, note = "") {
  return apiFetch<ApiOrder>(`/api/merchant/orders/${publicId}/status/`, {
    method: "PATCH",
    body: { status, note },
  });
}

export function fetchNextAction(publicId: string) {
  return apiFetch<NextAction>(`/api/merchant/orders/${publicId}/next-action/`);
}

/** A stable key for one checkout attempt. */
export function newIdempotencyKey() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `rb-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function hasRole(user: ApiUser | null, ...roles: UserRole[]) {
  return Boolean(user && roles.includes(user.role));
}