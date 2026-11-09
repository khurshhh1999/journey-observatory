import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { copy } from "@/content/copy";
import "@/styles/globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"], axes: ["opsz"] });

export const metadata: Metadata = {
  title: { default: copy.title, template: `%s · ${copy.title}` },
  description: copy.description,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full bg-background-full text-text-primary">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
