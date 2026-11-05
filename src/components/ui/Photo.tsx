"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/format";
import { artPalette, FoodArt } from "@/components/ui/FoodArt";

interface PhotoProps {
  src?: string | null;
  alt: string;
  art?: string;
  className?: string;
  banner?: boolean;
}

export function Photo({ src, alt, art = "hot-cup", className, banner }: PhotoProps) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const failed = Boolean(src) && failedSrc === src;

  useEffect(() => {
    if (!src) return;
    let active = true;
    const probe = new window.Image();
    probe.onerror = () => {
      if (active) setFailedSrc(src);
    };
    probe.src = src;
    return () => {
      active = false;
    };
  }, [src]);

  if (!src || failed) {
    return <FoodArt variant={art} className={className} banner={banner} />;
  }

  const palette = artPalette(art);
  const hasHeight = /(^|\s)h-/.test(className ?? "");
  return (
    <div
      role="img"
      aria-label={alt}
      className={cn(
        "bg-cover bg-center",
        banner ? cn(!hasHeight && "h-full", "w-full") : "aspect-square",
        className,
      )}
      style={{
        backgroundColor: palette.from,
        backgroundImage: `url("${src}")`,
      }}
    />
  );
}
