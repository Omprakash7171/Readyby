import {
  Benefits,
  FinalCta,
  ForCafes,
  HowItWorks,
  UseCase,
} from "@/components/landing/Sections";
import { Hero } from "@/components/landing/Hero";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <ForCafes />
      <Benefits />
      <UseCase />
      <FinalCta />
    </>
  );
}
