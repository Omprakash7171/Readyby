"use client";

import { useEffect, useState } from "react";
import { Plus, RefreshCw, Trash2, UtensilsCrossed } from "lucide-react";
import {
  ApiError,
  createMenuItem,
  deleteMenuItem,
  fetchMerchantMenu,
  updateMenuItem,
} from "@/lib/api";
import type { ApiMenuItem, MerchantMenuInput } from "@/lib/apiTypes";
import { formatPrice } from "@/lib/format";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Select, Textarea } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { Photo } from "@/components/ui/Photo";

const EMPTY: MerchantMenuInput = {
  name: "",
  description: "",
  price: "",
  category: "Coffee",
  image_url: "",
  prep_time_minutes: 3,
  is_available: true,
  is_popular: false,
};

export default function MerchantMenuPage() {
  const session = useRequireSession(["MERCHANT", "ADMIN"]);
  const [items, setItems] = useState<ApiMenuItem[] | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [editing, setEditing] = useState<ApiMenuItem | null>(null);
  const [form, setForm] = useState<MerchantMenuInput>(EMPTY);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const body = await fetchMerchantMenu(controller.signal);
        if (controller.signal.aborted) return;
        setItems(body.results);
        setCategories(body.categories);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "We couldn't load the menu. Check that the API is running.",
        );
      }
    })();
    return () => controller.abort();
  }, [session.user, reloadToken]);

  function startCreate() {
    setEditing(null);
    setForm(EMPTY);
    setFormError(null);
    setFieldErrors({});
    setOpen(true);
  }

  function startEdit(item: ApiMenuItem) {
    setEditing(item);
    setForm({
      name: item.name,
      description: item.description,
      price: item.price,
      category: item.category,
      image_url: item.image_url,
      prep_time_minutes: item.prep_time_minutes,
      is_available: item.is_available,
      is_popular: item.is_popular,
    });
    setFormError(null);
    setFieldErrors({});
    setOpen(true);
  }

  async function save() {
    setSaving(true);
    setFormError(null);
    setFieldErrors({});
    try {
      if (editing) {
        await updateMenuItem(editing.id, form);
      } else {
        await createMenuItem(form);
      }
      setOpen(false);
      setReloadToken((n) => n + 1);
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.message);
        setFieldErrors(err.fieldErrors);
      } else {
        setFormError("That item could not be saved.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function toggleAvailable(item: ApiMenuItem) {
    setBusyId(item.id);
    setError(null);
    try {
      const updated = await updateMenuItem(item.id, {
        is_available: !item.is_available,
      });
      setItems((current) =>
        current?.map((row) => (row.id === item.id ? updated : row)) ?? current,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That change could not be saved.");
    } finally {
      setBusyId(null);
    }
  }

  async function remove(item: ApiMenuItem) {
    if (!window.confirm(`Remove ${item.name} from the menu?`)) return;
    setBusyId(item.id);
    setError(null);
    try {
      await deleteMenuItem(item.id);
      setItems((current) => current?.filter((row) => row.id !== item.id) ?? current);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That item could not be removed.");
    } finally {
      setBusyId(null);
    }
  }

  if (session.pending) return null;

  const grouped = (categories.length ? categories : ["Menu"]).map((category) => ({
    category,
    rows: (items ?? []).filter((item) => item.category === category),
  }));

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-[-0.035em] text-ink-900">Menu</h1>
          <p className="mt-1.5 text-pretty text-ink-500">
            Keep drinks, food and preparation times current. Customers see changes
            immediately.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setReloadToken((n) => n + 1)}>
            <RefreshCw className="size-4" aria-hidden />
            Refresh
          </Button>
          <Button onClick={startCreate}>
            <Plus className="size-4" aria-hidden />
            Add item
          </Button>
        </div>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {items === null ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {[0, 1, 2, 3].map((n) => (
            <div key={n} className="h-28 animate-pulse rounded-3xl bg-ink-100" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <Card className="flex flex-col items-center px-6 py-16 text-center">
          <span className="grid size-14 place-items-center rounded-2xl bg-crema-100 text-ink-400">
            <UtensilsCrossed className="size-6" aria-hidden />
          </span>
          <h2 className="mt-4 text-lg font-semibold text-ink-900">Your menu is empty</h2>
          <p className="mt-1 max-w-sm text-sm text-ink-500">
            Add the first item so customers can order from your cafe.
          </p>
          <Button className="mt-5" onClick={startCreate}>
            <Plus className="size-4" aria-hidden />
            Add the first item
          </Button>
        </Card>
      ) : (
        <div className="space-y-7">
          {grouped.map(({ category, rows }) =>
            rows.length === 0 ? null : (
              <section key={category}>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
                    {category}
                  </h2>
                  <span className="text-sm text-ink-400">{rows.length}</span>
                </div>
                <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                  {rows.map((item) => (
                    <li key={item.id}>
                      <Card className="flex gap-3 p-3.5">
                        <Photo
                          src={item.image_url}
                          alt={item.name}
                          art={item.art}
                          className="size-20 shrink-0 rounded-2xl"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <h3 className="truncate font-semibold text-ink-900">{item.name}</h3>
                                {!item.is_available ? <Badge tone="danger">Sold out</Badge> : null}
                                {item.is_popular ? <Badge tone="brand">Popular</Badge> : null}
                              </div>
                              <p className="mt-0.5 line-clamp-1 text-xs text-ink-500">
                                {item.description || "No description"}
                              </p>
                            </div>
                            <p className="shrink-0 text-sm font-semibold text-ink-900">
                              {formatPrice(Number(item.price))}
                            </p>
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-1.5">
                            <Badge tone="neutral">{item.prep_time_minutes} min prep</Badge>
                            <button
                              type="button"
                              disabled={busyId === item.id}
                              onClick={() => void toggleAvailable(item)}
                              className="rounded-full px-2 py-1 text-xs font-medium text-brand-600 hover:bg-brand-50 disabled:opacity-50"
                            >
                              {item.is_available ? "Mark sold out" : "Bring back"}
                            </button>
                            <button
                              type="button"
                              onClick={() => startEdit(item)}
                              className="rounded-full px-2 py-1 text-xs font-medium text-ink-600 hover:bg-ink-100"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              disabled={busyId === item.id}
                              onClick={() => void remove(item)}
                              className="ml-auto rounded-full p-1.5 text-ink-300 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                              aria-label={`Remove ${item.name}`}
                            >
                              <Trash2 className="size-3.5" aria-hidden />
                            </button>
                          </div>
                        </div>
                      </Card>
                    </li>
                  ))}
                </ul>
              </section>
            ),
          )}
        </div>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? `Edit ${editing.name}` : "Add a menu item"}
        description="Prices and preparation times are saved exactly as entered."
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => void save()} disabled={saving}>
              {saving ? "Saving..." : editing ? "Save changes" : "Add item"}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {formError ? (
            <p role="alert" className="rounded-2xl bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </p>
          ) : null}
          <Field label="Name" htmlFor="menu-name">
            <Input
              id="menu-name"
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Flat white"
            />
            <FieldError errors={fieldErrors.name} />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Price" htmlFor="menu-price">
              <Input
                id="menu-price"
                inputMode="decimal"
                value={form.price}
                onChange={(event) => setForm({ ...form, price: event.target.value })}
                placeholder="3.20"
              />
              <FieldError errors={fieldErrors.price} />
            </Field>
            <Field label="Category" htmlFor="menu-category">
              <Input
                id="menu-category"
                value={form.category}
                onChange={(event) => setForm({ ...form, category: event.target.value })}
                placeholder="Coffee"
              />
            </Field>
          </div>
          <Field label="Description" htmlFor="menu-description">
            <Textarea
              id="menu-description"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Double shot, steamed milk, thin foam"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Prep time (minutes)" htmlFor="menu-prep" hint="Per item, not per order.">
              <Input
                id="menu-prep"
                type="number"
                min={1}
                max={120}
                value={form.prep_time_minutes}
                onChange={(event) =>
                  setForm({ ...form, prep_time_minutes: Number(event.target.value) })
                }
              />
              <FieldError errors={fieldErrors.prep_time_minutes} />
            </Field>
            <Field label="Availability" htmlFor="menu-available">
              <Select
                id="menu-available"
                value={form.is_available ? "yes" : "no"}
                onChange={(event) =>
                  setForm({ ...form, is_available: event.target.value === "yes" })
                }
              >
                <option value="yes">Available</option>
                <option value="no">Sold out</option>
              </Select>
            </Field>
          </div>
          <Field
            label="Photo URL"
            htmlFor="menu-image"
            hint="Optional. Leave blank to use the illustrated menu art."
          >
            <Input
              id="menu-image"
              value={form.image_url}
              onChange={(event) => setForm({ ...form, image_url: event.target.value })}
              placeholder="https://..."
            />
            <FieldError errors={fieldErrors.image_url} />
          </Field>
          <label className="flex items-center gap-2.5 text-sm font-medium text-ink-700">
            <input
              type="checkbox"
              checked={form.is_popular}
              onChange={(event) => setForm({ ...form, is_popular: event.target.checked })}
              className="size-4 rounded border-ink-300 text-brand-500"
            />
            Mark as popular
          </label>
        </div>
      </Modal>
    </div>
  );
}

function FieldError({ errors }: { errors?: string[] }) {
  if (!errors?.length) return null;
  return <p className="text-xs text-red-600">{errors[0]}</p>;
}
