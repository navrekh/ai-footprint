import { ComingSoon } from "@/components/ComingSoon";

export function DocumentationPage() {
  return (
    <ComingSoon
      title="Documentation"
      description="Reference material for the API, SDK and estimation methodology."
      capabilities={[
        "Quick start and authentication reference",
        "Endpoint reference generated from the OpenAPI contract",
        "Methodology, assumptions and provenance documentation",
      ]}
    />
  );
}
