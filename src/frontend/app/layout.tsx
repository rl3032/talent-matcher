"use client";

import "./globals.css";
import { AuthProvider } from "../lib/AuthContext";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>Talent Matcher</title>
        <meta
          name="description"
          content="Find perfect matches between candidates and jobs"
        />
      </head>
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
