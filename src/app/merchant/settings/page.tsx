"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Store } from "lucide-react";
import { ApiError, fetchMyCafe, updateMyCafe } from "@/lib/api";
import type { MerchantCafe, MerchantCafeInput } from "@/lib/apiTypes";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Textarea } from "@/components/ui/Field";
import { Photo } from "@/components/ui/Photo";

export default function MerchantSettingsPage() {
  const session = useRequireSession(["MERCHANT", "ADMIN"]);
  const [cafe, setCafe] = useState<MerchantCafe | null>(null);
  const [form, setForm] = useState<MerchantCafeInput>({});
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!session.user) return;
    void (async () => {
      try {
        const body = await fetchMyCafe();
        setCafe(body);
        setForm({
          name: body.name,
          tagline: body.tagline,
          category: body.category,
          description: body.description,
          image_url: body.image_url,
          address: body.address,
          postcode: body.postcode,
          prep_time_minutes: body.prep_time_minutes,
          kitchen_capacity: body.kitchen_capacity,
          slot_capacity: body.slot_capacity,
        });
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "We couldn't load your cafe settings. Check that the API is running.",
        );
      }
    })();
  }, [session.user]);

  function update<K extends keyof MerchantCafeInput>(
    key: K,
    value: MerchantCafeInput[K],
  ) {
    setSaved(false);
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function save() {
    setSaving(true);
    setError(null);
    setFieldErrors({});
    try {
      const body = await updateMyCafe(form);
      setCafe(body);
      setSaved(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setFieldErrors(err.fieldErrors);
      } else {
        setError("Those settings could not be saved.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (session.pending) return null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-[-0.035em] text-ink-900">
          Cafe settings
        </h1>
        <p className="mt-1.5 max-w-2xl text-pretty text-ink-500">
          The details customers see, plus the kitchen limits that shape every
          pickup estimate.
        </p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}
      {saved ? (
        <p className="flex items-center gap-2 rounded-2xl border border-ready-200 bg-ready-50 px-4 py-3 text-sm text-ready-700">
          <CheckCircle2 className="size-4" aria-hidden />
          Cafe settings saved.
        </p>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_18rem] xl:items-start">
        <Card className="p-5 sm:p-6">
          <div className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Cafe name" htmlFor="cafe-name">
                <Input
                  id="cafe-name"
                  value={form.name ?? ""}
                  onChange={(event) => update("name", event.target.value)}
                />
                <FieldError errors={fieldErrors.name} />
              </Field>
              <Field label="Category" htmlFor="cafe-category">
                <Input
                  id="cafe-category"
                  value={form.category ?? ""}
                  onChange={(event) => update("category", event.target.value)}
                  placeholder="Coffee & Bakery"
                />
              </Field>
            </div>
            <Field label="Tagline" htmlFor="cafe-tagline">
              <Input
                id="cafe-tagline"
                value={form.tagline ?? ""}
                onChange={(event) => update("tagline", event.target.value)}
                placeholder="Coffee & Bakery"
              />
            </Field>
            <Field label="Description" htmlFor="cafe-description">
              <Textarea
                id="cafe-description"
                value={form.description ?? ""}
                onChange={(event) => update("description", event.target.value)}
                placeholder="Tell customers what makes your cafe worth the walk."
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-[1fr_10rem]">
              <Field label="Address" htmlFor="cafe-address">
                <Input
                  id="cafe-address"
                  value={form.address ?? ""}
                  onChange={(event) => update("address", event.target.value)}
                />
              </Field>
              <Field label="Postcode" htmlFor="cafe-postcode">
                <Input
                  id="cafe-postcode"
                  value={form.postcode ?? ""}
                  onChange={(event) => update("postcode", event.target.value)}
                />
              </Field>
            </div>
            <Field
              label="Cover photo URL"
              htmlFor="cafe-image"
              hint="Optional. Used on your shop page and dashboard."
            >
              <Input
                id="cafe-image"
                value={form.image_url ?? ""}
                onChange={(event) => update("image_url", event.target.value)}
                placeholder="https://..."
              />
              <FieldError errors={fieldErrors.image_url} />
            </Field>

            <div className="border-t border-ink-100 pt-5">
              <h2 className="font-semibold tracking-[-0.02em] text-ink-900">
                Kitchen and pickup limits
              </h2>
              <p className="mt-1 text-sm text-ink-500">
                These values are used to calculate preparation time and how many
                orders can arrive together.
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <Field label="Fallback prep (min)" htmlFor="cafe-prep">
                  <Input
                    id="cafe-prep"
                    type="number"
                    min={1}
                    max={120}
                    value={form.prep_time_minutes ?? 8}
                    onChange={(event) =>
                      update("prep_time_minutes", Number(event.target.value))
                    }
                  />
                </Field>
                <Field label="Kitchen capacity" htmlFor="cafe-kitchen" hint="Items at once.">
                  <Input
                    id="cafe-kitchen"
                    type="number"
                    min={1}
                    max={20}
                    value={form.kitchen_capacity ?? 4}
                    onChange={(event) =>
                      update("kitchen_capacity", Number(event.target.value))
                    }
                  />
                  <FieldError errors={fieldErrors.kitchen_capacity} />
                </Field>
                <Field label="Slot capacity" htmlFor="cafe-slot" hint="Orders per 15 min.">
                  <Input
                    id="cafe-slot"
                    type="number"
                    min={1}
                    max={100}
                    value={form.slot_capacity ?? 6}
                    onChange={(event) =>
                      update("slot_capacity", Number(event.target.value))
                    }
                  />
                  <FieldError errors={fieldErrors.slot_capacity} />
                </Field>
              </div>
            </div>

            <div className="flex justify-end border-t border-ink-100 pt-5">
              <Button onClick={() => void save()} disabled={saving}>
                {saving ? "Saving..." : "Save settings"}
              </Button>
            </div>
          </div>
        </Card>

        <aside className="space-y-4">
          <Card className="overflow-hidden">
            <Photo
              src={form.image_url}
              alt={form.name ? `${form.name} interior` : "Cafe interior"}
              art="latte"
              banner
              className="h-40"
            />
            <div className="p-5">
              <div className="flex items-start gap-2">
                <Store className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden />
                <div>
                  <p className="font-semibold text-ink-900">{form.name || "Your cafe"}</p>
                  <p className="mt-1 text-sm text-ink-500">
                    {form.address || "Add your address"}
                    {form.postcode ? `, ${form.postcode}` : ""}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {cafe?.is_demo ? <Badge tone="brand">Demo cafe</Badge> : null}
                <Badge tone={cafe?.is_active ? "ready" : "danger"}>
                  {cafe?.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <p className="mt-4 text-xs leading-relaxed text-ink-400">
                {cafe?.opening_hours_summary ?? "Opening hours are managed by ReadyBy."}
              </p>
            </div>
          </Card>
          <p className="px-2 text-xs leading-relaxed text-ink-400">
            Opening hours and cafe visibility are managed by ReadyBy. Ask an admin
            if they need to change.
          </p>
        </aside>
      </div>
    </div>
  );
}

function FieldError({ errors }: { errors?: string[] }) {
  if (!errors?.length) return null;
  return <p className="text-xs text-red-600">{errors[0]}</p>;
}
