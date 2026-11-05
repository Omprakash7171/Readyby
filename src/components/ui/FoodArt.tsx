import { cn } from "@/lib/format";

/** The illustration keys the API stores on a menu item. */
export type ArtVariant =
  | "hot-cup"
  | "latte"
  | "cappuccino"
  | "cold-cup"
  | "croissant"
  | "pain-au-chocolat"
  | "sandwich"
  | "muffin"
  | "tea"
  | "hot-chocolate"
  | "cookie"
  | "toastie"
  | "bowl";

const PALETTES: Record<ArtVariant, { from: string; to: string; accent: string }> =
  {
    "hot-cup": { from: "#fdf0e4", to: "#f6dcc6", accent: "#8a5a3b" },
    cappuccino: { from: "#fbeee2", to: "#f2d9c1", accent: "#8a5a3b" },
    latte: { from: "#f8ece0", to: "#eed6bd", accent: "#7c4f33" },
    "cold-cup": { from: "#eaf3f5", to: "#d5e7ec", accent: "#3f6b78" },
    croissant: { from: "#fdf3e2", to: "#f7e0b8", accent: "#b9743a" },
    "pain-au-chocolat": { from: "#fdf1de", to: "#f4d9b0", accent: "#a96430" },
    sandwich: { from: "#fdf1e0", to: "#f6dcb8", accent: "#b06b34" },
    toastie: { from: "#fcefdd", to: "#f3d5a9", accent: "#a8642e" },
    muffin: { from: "#fdeee3", to: "#f6d9c8", accent: "#8f5b46" },
    tea: { from: "#eef4ec", to: "#d9e8d6", accent: "#4f7355" },
    "hot-chocolate": { from: "#f7ebe4", to: "#edd6c6", accent: "#7a4a30" },
    cookie: { from: "#fdf1de", to: "#f2d8ae", accent: "#9c6330" },
    bowl: { from: "#eef5ef", to: "#dcebdd", accent: "#4f7a5c" },
  };

function Artwork({ variant }: { variant: ArtVariant }) {
  switch (variant) {
    case "cold-cup":
      return (
        <>
          <path d="M24 16h18l-3 34a4 4 0 0 1-4 3.6h-4A4 4 0 0 1 27 50z" fill="#ffffff" stroke="#3f6b78" strokeWidth="2" strokeLinejoin="round" />
          <path d="M25.4 30h15.2l-1.6 20a4 4 0 0 1-4 3.6h-4a4 4 0 0 1-4-3.6z" fill="#a9d4e0" />
          <rect x="27" y="22" width="6" height="6" rx="1.6" fill="#ffffff" opacity="0.9" transform="rotate(-12 30 25)" />
          <rect x="35" y="25" width="5" height="5" rx="1.4" fill="#ffffff" opacity="0.9" transform="rotate(9 37 27)" />
          <path d="M35 16 44 5" stroke="#e1552e" strokeWidth="3" strokeLinecap="round" />
          <path d="M23 16h20" stroke="#3f6b78" strokeWidth="2.6" strokeLinecap="round" />
        </>
      );
    case "croissant":
      return (
        <g>
          <path
            d="M8 44c2-14 12-24 24-24s22 10 24 24c-6 3-12 4-18 3-2 4-4 4-6 0-6 1-12 0-18-3z"
            fill="#e8a35c"
            stroke="#b9743a"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M20 24c-2 5-3 11-3 18" stroke="#b9743a" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M44 24c2 5 3 11 3 18" stroke="#b9743a" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M32 20c-4 0-7 1-10 3" stroke="#b9743a" strokeWidth="1.8" strokeLinecap="round" />
        </g>
      );
    case "pain-au-chocolat":
      return (
        <g>
          <rect x="10" y="22" width="44" height="26" rx="12" fill="#eeb877" stroke="#a96430" strokeWidth="2" />
          <rect x="18" y="27" width="11" height="16" rx="4" fill="#5b3520" />
          <rect x="35" y="27" width="11" height="16" rx="4" fill="#5b3520" />
          <path d="M10 32c8-6 20-8 44-6" stroke="#a96430" strokeWidth="1.6" opacity="0.6" fill="none" />
        </g>
      );
    case "sandwich":
      return (
        <g>
          <path d="M10 46h44l-6 8H16z" fill="#e7a85e" stroke="#b06b34" strokeWidth="2" strokeLinejoin="round" />
          <path d="M12 38h40l-2 8H14z" fill="#f6d9a4" />
          <path d="M12 30h40l-4 8H16z" fill="#8fbf6a" />
          <path d="M14 24c6-6 30-6 36 0 2 2 2 6 0 6H14c-2 0-2-4 0-6z" fill="#f3c78c" stroke="#b06b34" strokeWidth="2" strokeLinejoin="round" />
          <path d="M24 24v6M32 23v7M40 24v6" stroke="#b06b34" strokeWidth="1.4" opacity="0.7" />
        </g>
      );
    case "toastie":
      return (
        <g>
          <rect x="14" y="16" width="36" height="32" rx="8" fill="#f0c78c" stroke="#a8642e" strokeWidth="2" />
          <path d="M14 26h36M14 38h36" stroke="#a8642e" strokeWidth="1.8" />
          <path d="M24 16 20 48M40 16l4 32" stroke="#a8642e" strokeWidth="1.6" opacity="0.65" />
          <path d="M22 20l20 24" stroke="#f7e3bd" strokeWidth="4" opacity="0.55" strokeLinecap="round" />
        </g>
      );
    case "muffin":
      return (
        <g>
          <path d="M14 34h36l-3 18a4 4 0 0 1-4 3H21a4 4 0 0 1-4-3z" fill="#d9a97c" stroke="#8f5b46" strokeWidth="2" strokeLinejoin="round" />
          <path d="M12 34c0-10 9-16 20-16s20 6 20 16z" fill="#e9c79c" stroke="#8f5b46" strokeWidth="2" strokeLinejoin="round" />
          <circle cx="26" cy="26" r="2.6" fill="#5b3520" />
          <circle cx="37" cy="30" r="2.4" fill="#5b3520" />
          <circle cx="32" cy="21" r="2.2" fill="#5b3520" />
          <path d="M20 38v14M44 38v14" stroke="#8f5b46" strokeWidth="1.4" opacity="0.6" />
        </g>
      );
    case "tea":
      return (
        <g>
          <path d="M20 22h24l-3 26a5 5 0 0 1-5 4h-8a5 5 0 0 1-5-4z" fill="#ffffff" stroke="#4f7355" strokeWidth="2" strokeLinejoin="round" />
          <path d="M22 32h20l-2.4 16a5 5 0 0 1-5 4h-5a5 5 0 0 1-5-4z" fill="#b98a4f" />
          <path d="M44 30c5 0 6 10 0 12" fill="none" stroke="#4f7355" strokeWidth="2" strokeLinecap="round" />
          <path d="M17 22h30" stroke="#4f7355" strokeWidth="2.6" strokeLinecap="round" />
          <path d="M26 18c0-3 3-4 3-7M36 18c0-3 3-4 3-7" stroke="#4f7355" strokeWidth="1.8" strokeLinecap="round" opacity="0.7" />
        </g>
      );
    case "hot-chocolate":
      return (
        <g>
          <rect x="16" y="24" width="32" height="28" rx="7" fill="#ffffff" stroke="#7a4a30" strokeWidth="2" />
          <path d="M19 34h26v11a7 7 0 0 1-7 7h-12a7 7 0 0 1-7-7z" fill="#8a5a3b" />
          <circle cx="26" cy="31" r="4" fill="#ffffff" />
          <circle cx="36" cy="31" r="4" fill="#ffffff" />
          <path d="M48 30c5 1 5 11 0 12" fill="none" stroke="#7a4a30" strokeWidth="2" strokeLinecap="round" />
          <path d="M26 20c0-3 3-4 3-7M36 20c0-3 3-4 3-7" stroke="#7a4a30" strokeWidth="1.8" strokeLinecap="round" opacity="0.6" />
        </g>
      );
    case "cookie":
      return (
        <g>
          <circle cx="32" cy="33" r="21" fill="#e2ad72" stroke="#9c6330" strokeWidth="2" />
          <circle cx="24" cy="27" r="3.2" fill="#5b3520" />
          <circle cx="38" cy="24" r="2.8" fill="#5b3520" />
          <circle cx="41" cy="38" r="3.4" fill="#5b3520" />
          <circle cx="27" cy="41" r="3" fill="#5b3520" />
          <circle cx="18" cy="37" r="2.4" fill="#5b3520" />
        </g>
      );
    case "bowl":
      return (
        <g>
          <path d="M12 34h40c0 12-9 20-20 20s-20-8-20-20z" fill="#ffffff" stroke="#4f7a5c" strokeWidth="2" strokeLinejoin="round" />
          <path d="M12 34h40c0 3-1 6-2 8H14c-1-2-2-5-2-8z" fill="#8fbf6a" />
          <circle cx="26" cy="30" r="5" fill="#e1552e" />
          <circle cx="38" cy="30" r="5" fill="#f2b33d" />
          <circle cx="32" cy="25" r="4" fill="#ffffff" />
          <path d="M26 20c-1-4 4-6 6-3" stroke="#4f7a5c" strokeWidth="1.8" strokeLinecap="round" fill="none" />
        </g>
      );
    case "cappuccino":
      return (
        <g>
          <path d="M18 26h28l-3.5 24a6 6 0 0 1-6 5h-9a6 6 0 0 1-6-5z" fill="#ffffff" stroke="#8a5a3b" strokeWidth="2" strokeLinejoin="round" />
          <path d="M20.5 36h23l-2.6 14a6 6 0 0 1-6 5h-6a6 6 0 0 1-6-5z" fill="#cfa27a" />
          <path d="M32 42c-3-2.5-6 1-3 3.5 1.6 1.4 3 2 3 2s1.4-.6 3-2c3-2.5 0-6-3-3.5z" fill="#ffffff" />
          <path d="M46 32c5 0 6 10 0 12" fill="none" stroke="#8a5a3b" strokeWidth="2" strokeLinecap="round" />
          <path d="M15 26h34" stroke="#8a5a3b" strokeWidth="2.8" strokeLinecap="round" />
        </g>
      );
    case "latte":
    default:
      return (
        <g>
          <path d="M18 26h28l-3.5 24a6 6 0 0 1-6 5h-9a6 6 0 0 1-6-5z" fill="#ffffff" stroke="#7c4f33" strokeWidth="2" strokeLinejoin="round" />
          <path d="M20.5 36h23l-2.6 14a6 6 0 0 1-6 5h-6a6 6 0 0 1-6-5z" fill="#a9764c" />
          <path d="M21.5 33c4-3 8-4 10.5-4s6.5 1 10.5 4c-1.6 2-5.5 3-10.5 3s-8.9-1-10.5-3z" fill="#e6cdb2" />
          <path d="M46 32c5 0 6 10 0 12" fill="none" stroke="#7c4f33" strokeWidth="2" strokeLinecap="round" />
          <path d="M15 26h34" stroke="#7c4f33" strokeWidth="2.8" strokeLinecap="round" />
          <path d="M26 20c0-3 3-4 3-7M36 20c0-3 3-4 3-7" stroke="#7c4f33" strokeWidth="1.8" strokeLinecap="round" opacity="0.55" />
        </g>
      );
  }
}

interface FoodArtProps {
  /** The API stores this as a string, so an unknown key falls back gracefully. */
  variant: string;
  className?: string;
  /** Renders a wide banner tile instead of a square swatch. */
  banner?: boolean;
}

/**
 * Lightweight inline illustration used in place of photography.
 * Callers must supply their own width/height (e.g. `size-11`, `h-32 w-full`);
 * `className` is intentionally the last word on sizing so nothing here can
 * override it.
 */
export function FoodArt({ variant, className, banner }: FoodArtProps) {
  const known = variant in PALETTES ? (variant as ArtVariant) : "hot-cup";
  const palette = PALETTES[known];

  return (
    <div
      aria-hidden
      className={cn(
        "relative overflow-hidden",
        banner ? "h-full w-full" : "aspect-square",
        className,
      )}
      style={{
        backgroundImage: `linear-gradient(150deg, ${palette.from}, ${palette.to})`,
      }}
    >
      <span
        className="absolute -top-6 -right-6 size-16 rounded-full opacity-50"
        style={{ backgroundColor: "#ffffff" }}
      />
      <svg
        viewBox="0 0 64 64"
        className={cn(
          "relative h-full w-full",
          banner ? "scale-105" : "p-[12%]",
        )}
        preserveAspectRatio="xMidYMid meet"
      >
        <Artwork variant={known} />
      </svg>
    </div>
  );
}

export function artPalette(variant: string) {
  return PALETTES[variant in PALETTES ? (variant as ArtVariant) : "hot-cup"];
}