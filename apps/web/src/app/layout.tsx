import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EduKit",
  description: "Local-first digital transformation for schools.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
