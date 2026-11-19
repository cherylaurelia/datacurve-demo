import type { Metadata } from "next";
import { Google_Sans_Code } from "next/font/google";
import "./globals.css";

const sansCode = Google_Sans_Code({ subsets: ["latin"], variable: "--font-gsc" });

export const metadata: Metadata = {
  title: "DeepSWE egress check: one v1.1 row ran with the network open (unofficial)",
  description:
    "A check of DeepSWE v1.1's published trajectories for network access in no-network tasks. Unofficial, by Cheryl Aurelia.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sansCode.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
