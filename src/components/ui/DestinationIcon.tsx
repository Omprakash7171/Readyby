import {
  Building2,
  Dumbbell,
  GraduationCap,
  Scissors,
  TrainFront,
} from "lucide-react";

/** The icon keys the API stores on a `Destination`. */
export type DestinationIconKey =
  | "scissors"
  | "building"
  | "graduation"
  | "dumbbell"
  | "train";

const ICONS = {
  scissors: Scissors,
  building: Building2,
  graduation: GraduationCap,
  dumbbell: Dumbbell,
  train: TrainFront,
} satisfies Record<DestinationIconKey, typeof Scissors>;

export function DestinationIcon({
  icon,
  className,
}: {
  icon: string;
  className?: string;
}) {
  const Icon = ICONS[icon as DestinationIconKey] ?? Building2;
  return <Icon className={className} aria-hidden />;
}