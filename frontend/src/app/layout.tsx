import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BundCheck — Probabilistic Content Inspection & Writing Quality Platform",
  description:
    "Rigorous, calibrated AI-pattern inspection and precision writing improvement with deterministic span preservation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-background text-text-primary antialiased font-sans selection:bg-accent/30 selection:text-text-primary">
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
