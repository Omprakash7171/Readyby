/**
 * Types mirroring the Django API payloads exactly.
 *
 * Money arrives as a string so the browser never rounds a float. Anything the
 * backend owns (prices, totals, timings, status copy) is used verbatim — never
 * recomputed here.
 */

export type UserRole = "CUSTOMER" | "MERCHANT" | "ADMIN";

/** Explicit account state. Mirrors `is_active`, which is never sent separately. */
export type AccountStatus = "ACTIVE" | "SUSPENDED";

export interface ApiUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  /** Composed by the API from the two fields above. Never edited directly. */
  full_name: string;
  display_name: string;
  initials: string;
  role: UserRole;
  status: AccountStatus;
  is_active: boolean;
  phone: string;
  created_at: string;
  cafe: { slug: string; name: string; is_active: boolean } | null;
}

/** The editable fields on your own account. Everything else is server-owned. */
export interface ProfileUpdateInput {
  first_name?: string;
  last_name?: string;
  phone?: string;
  password?: string;
  confirm_password?: string;
  current_password?: string;
}

export interface AuthResponse {
  /** Opaque DRF token. Sent as `Authorization: Token <token>`. */
  token: string;
  /** JWT access token. Sent as `Authorization: Bearer <access>`. */
  access: string;
  /** JWT refresh token, exchanged at /api/auth/token/refresh/. */
  refresh: string;
  user: ApiUser;
}

export interface ApiDestination {
  id: number;
  key: string;
  name: string;
  kind: string;
  area: string;
  note: string;
  icon: string;
}

export interface DestinationListResponse {
  count: number;
  results: ApiDestination[];
}

export type OpenState = "open" | "closing-soon" | "closed" | null;

export interface ApiCafe {
  id: number;
  slug: string;
  name: string;
  tagline: string;
  category: string;
  description: string;
  image_url: string;
  address: string;
  postcode: string;
  latitude: string | null;
  longitude: string | null;
  rating: string;
  review_count: number;
  prep_time_minutes: number;
  kitchen_capacity: number;
  slot_capacity: number;
  opening_hours: Record<string, unknown> | null;
  opening_hours_summary: string;
  open_state: OpenState;
  open_state_label: string | null;
  is_active: boolean;
  is_demo: boolean;
  distance_metres: number | null;
  distance_label: string | null;
  walk_minutes: number | null;
  arrival_time: string | null;
  start_preparing_time: string | null;
  start_preparing_time_label: string | null;
  estimated_ready_time: string | null;
  estimated_ready_time_label: string | null;
  available_pickup_time: string | null;
  available_pickup_time_label: string | null;
  can_order: boolean;
  unavailable_reason: string | null;
  checked_at: string | null;
}

export interface CafeListResponse {
  count: number;
  destination: ApiDestination | null;
  arrival_time: string | null;
  results: ApiCafe[];
}

export interface ApiMenuItem {
  id: number;
  name: string;
  description: string;
  price: string;
  category: string;
  art: string;
  image_url: string;
  prep_time_minutes: number;
  is_available: boolean;
  is_popular: boolean;
  tag: string | null;
}

export interface MerchantMenuResponse {
  cafe: string;
  count: number;
  categories: string[];
  results: ApiMenuItem[];
}

export interface MerchantMenuInput {
  name: string;
  description: string;
  price: string;
  category: string;
  image_url: string;
  prep_time_minutes: number;
  is_available: boolean;
  is_popular: boolean;
}

export interface CafeMenuResponse {
  cafe: ApiCafe;
  categories: string[];
  items: ApiMenuItem[];
}

export type OrderStatus =
  | "PLACED"
  | "ACCEPTED"
  | "PREPARING"
  | "READY"
  | "COLLECTED"
  | "REJECTED"
  | "CANCELLED";

export interface ApiOrderItem {
  id: number;
  menu_item: number;
  name: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  art: string;
}

export interface ApiOrderEvent {
  status: OrderStatus;
  status_label: string;
  note: string;
  created_at: string;
  created_at_label: string;
}

export interface TrackingStep {
  status: OrderStatus;
  label: string;
}

export interface ApiOrder {
  id: number;
  public_id: string;
  status: OrderStatus;
  status_label: string;
  status_headline: string;
  status_message: string;
  progress_rank: number;
  tracking_steps: TrackingStep[];
  customer: { name: string; email: string };
  cafe: {
    slug: string;
    name: string;
    address: string;
    postcode: string;
    image_url: string;
  };
  destination: { key: string; name: string } | null;
  destination_label: string;
  items: ApiOrderItem[];
  item_count: number;
  subtotal: string;
  payment_method: string;
  payment_method_label: string;
  notes: string;
  arrival_time: string;
  arrival_time_label: string;
  arrival_day_label: string;
  prep_time_minutes: number;
  start_preparing_time: string;
  start_preparing_time_label: string;
  estimated_ready_time: string;
  estimated_ready_time_label: string;
  minutes_until_arrival: number | null;
  merchant_hint: string;
  created_at: string;
  updated_at: string;
  accepted_at: string | null;
  ready_at: string | null;
  collected_at: string | null;
  rejected_at: string | null;
  rejected_reason: string;
  cancelled_at: string | null;
  cancel_reason: string;
  events: ApiOrderEvent[];
}

export interface ApiOrderSummaryRow {
  public_id: string;
  status: OrderStatus;
  status_label: string;
  customer_name: string;
  cafe: { slug: string; name: string };
  items: string[];
  items_detailed: ApiOrderItem[];
  subtotal: string;
  destination_label: string;
  arrival_time: string;
  arrival_time_label: string;
  start_preparing_time: string;
  start_preparing_time_label: string;
  estimated_ready_time: string;
  estimated_ready_time_label: string;
  prep_time_minutes: number;
  minutes_until_arrival: number | null;
  merchant_hint: string;
  created_at: string;
  is_demo: boolean;
}

export interface OrderListResponse {
  count: number;
  results: ApiOrderSummaryRow[];
}

export interface ApiOrderStatus {
  public_id: string;
  status: OrderStatus;
  status_label: string;
  status_headline: string;
  status_message: string;
  progress_rank: number;
  estimated_ready_time: string;
  estimated_ready_time_label: string;
  arrival_time_label: string;
  minutes_until_arrival: number | null;
  updated_at: string;
}

export interface MerchantCafe {
  slug: string;
  name: string;
  tagline: string;
  category: string;
  description: string;
  image_url: string;
  address: string;
  postcode: string;
  prep_time_minutes: number;
  kitchen_capacity: number;
  slot_capacity: number;
  opening_hours: Record<string, unknown> | null;
  opening_hours_summary: string;
  is_active: boolean;
  is_demo: boolean;
}

export interface MerchantCafeInput {
  name?: string;
  tagline?: string;
  category?: string;
  description?: string;
  image_url?: string;
  address?: string;
  postcode?: string;
  prep_time_minutes?: number;
  kitchen_capacity?: number;
  slot_capacity?: number;
}

export interface PickupSlot {
  arrival_time: string;
  time_label: string;
  day_label: string;
  label: string;
  remaining: number;
  capacity: number;
}

export interface RequestedPickupSlot extends PickupSlot {
  problem: string | null;
  is_available: boolean;
}

export interface PickupQuote {
  cafe: string;
  prep_time_minutes: number;
  kitchen_capacity: number;
  slot_capacity: number;
  slot_interval_minutes: number;
  earliest_arrival_time: string;
  earliest_arrival_label: string;
  latest_arrival_time: string;
  latest_arrival_label: string;
  slots: PickupSlot[];
  requested_slot: RequestedPickupSlot | null;
  unavailable_items: string[];
  missing_item_ids: number[];
  is_accepting_orders: boolean;
}

export interface MerchantPickupSlot extends PickupSlot {
  booked: number;
  is_full: boolean;
}

export interface MerchantPickupSlots {
  cafe: string;
  slot_capacity: number;
  slot_interval_minutes: number;
  slots: MerchantPickupSlot[];
}

export interface NextAction {
  public_id: string;
  status: OrderStatus;
  next_status: OrderStatus | null;
  next_action_label: string | null;
  suggested_next_status: OrderStatus | null;
}

export interface BoardSummary {
  orders_today: number;
  dropped_today: number;
  revenue_today: string;
  pending: number;
  new: number;
  accepted: number;
  preparing: number;
  ready: number;
  collected: number;
  rejected: number;
  cancelled: number;
  generated_at: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  field_errors: Record<string, string[]>;
}