import { Outlet, createRootRoute, HeadContent, Scripts, Link } from "@tanstack/react-router";
import { Toaster } from "sonner";
import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="font-display text-7xl text-text-primary">404</h1>
        <h2 className="mt-2 text-xl text-text-primary">Page not found</h2>
        <p className="mt-2 text-sm text-text-secondary">
          This route does not exist in the TRIAGE environment.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary-dark"
        >
          Go home
        </Link>
      </div>
    </div>
  );
}

const FAVICON =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect x='9.5' y='3' width='5' height='18' fill='%23DC2626'/><rect x='3' y='9.5' width='18' height='5' fill='%23DC2626'/></svg>`,
  );

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "TRIAGE — AI Hospital Crisis Simulator | Meta PyTorch OpenEnv Hackathon" },
      {
        name: "description",
        content:
          "TRIAGE is a multi-agent hospital crisis simulation environment for training AI agents on coordinated mass casualty response.",
      },
      { property: "og:title", content: "TRIAGE — AI Hospital Crisis Simulator" },
      {
        property: "og:description",
        content:
          "Multi-agent hospital simulation built for the Meta PyTorch OpenEnv Hackathon 2025.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", type: "image/svg+xml", href: FAVICON },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: () => (
    <>
      <Outlet />
      <Toaster
        position="top-right"
        theme="system"
        toastOptions={{
          style: {
            background: "var(--surface)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            fontFamily: "DM Sans, sans-serif",
            fontSize: 13,
          },
        }}
      />
    </>
  ),
  notFoundComponent: NotFoundComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
