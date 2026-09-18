import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="py-20 text-center">
      <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">404</p>
      <h1 className="mt-3 text-xl font-semibold">Page not found</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        This console route does not exist.
      </p>
      <Button asChild className="mt-6">
        <Link to="/dashboard">Go to dashboard</Link>
      </Button>
    </div>
  );
}
