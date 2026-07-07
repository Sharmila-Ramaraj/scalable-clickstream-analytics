import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("http://scalable-real-time-clickstream-analytics-x24244066.s3-website-us-east-1.amazonaws.com"),
  title: "Scalable Real-Time Clickstream Analytics | X24244066",
  description: "A verified AWS Lambda architecture dashboard for e-commerce product trends, funnel drop-off, and PySpark performance.",
  openGraph: {
    title: "Scalable Real-Time Clickstream Analytics | X24244066",
    description: "Trending products, funnel drop-off and measured PySpark performance on AWS.",
    type: "website",
    images: [{ url: "/og.png", width: 1280, height: 945, alt: "Scalable real-time clickstream analytics dashboard" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Scalable Real-Time Clickstream Analytics | X24244066",
    description: "Trending products, funnel drop-off and measured PySpark performance on AWS.",
    images: ["/og.png"],
  },
};

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
