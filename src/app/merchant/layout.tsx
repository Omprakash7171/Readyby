import { MerchantShell } from "@/components/merchant/MerchantShell";

export default function MerchantLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <MerchantShell>{children}</MerchantShell>;
}
