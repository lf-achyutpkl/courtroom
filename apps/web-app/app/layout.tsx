import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Courtroom Simulation",
  description: "Transcript-driven courtroom playback with preview timing and PixiJS animation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex h-full flex-col">{children}</body>
    </html>
  );
}
