import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const metadataBase = new URL(`${protocol}://${host}`);

  return {
    metadataBase,
    title: "StreamCart | Real-Time Clickstream Analytics",
    description: "A verified AWS Lambda architecture dashboard for e-commerce product trends, funnel drop-off, and PySpark performance.",
    openGraph: {
      title: "StreamCart | Real-Time Clickstream Analytics",
      description: "Trending products, funnel drop-off and measured PySpark performance on AWS.",
      type: "website",
      images: [{ url: "/og.png", width: 1680, height: 945, alt: "StreamCart clickstream analytics dashboard" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "StreamCart | Real-Time Clickstream Analytics",
      description: "Trending products, funnel drop-off and measured PySpark performance on AWS.",
      images: ["/og.png"],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
