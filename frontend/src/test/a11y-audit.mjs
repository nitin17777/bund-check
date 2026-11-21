import { JSDOM } from "jsdom";
import axe from "axe-core";

const routes = [
  { path: "/", name: "Landing Page" },
  { path: "/dashboard", name: "Dashboard" },
  { path: "/checker", name: "Content Checker" },
  { path: "/humanizer", name: "Writing Improver" },
  { path: "/history", name: "Audit History" },
  { path: "/reports/demo-123", name: "Report Detail" },
  { path: "/settings", name: "Settings" },
];

async function runAudit() {
  console.log("=== BUNDCHECK ACCESSIBILITY & LIGHTHOUSE AUDIT ===");
  let allPassed = true;

  for (const route of routes) {
    const url = `http://localhost:3000${route.path}`;
    const res = await fetch(url);
    const html = await res.text();

    const dom = new JSDOM(html, {
      runScripts: "outside-only",
      url,
    });

    const { window } = dom;

    // Run axe accessibility analysis
    const results = await axe.run(window.document.documentElement, {
      rules: {
        // Exclude color-contrast since JSDOM does not render real CSS computed styles
        "color-contrast": { enabled: false },
      },
    });

    const violations = results.violations;
    const passes = results.passes.length;
    const score = Math.round((passes / (passes + violations.length)) * 100);

    console.log(`\nRoute: ${route.name} (${route.path})`);
    console.log(`  Accessibility Score: ${score}% (${passes} rules passed, ${violations.length} violations)`);

    if (violations.length > 0) {
      allPassed = false;
      console.log("  Violations:");
      for (const v of violations) {
        console.log(`    - [${v.id}] ${v.help} (Severity: ${v.impact})`);
        for (const node of v.nodes) {
          console.log(`      Target: ${node.target.join(", ")}`);
        }
      }
    } else {
      console.log("  ✓ No accessibility violations detected!");
    }
  }

  if (!allPassed) {
    process.exit(1);
  }
}

runAudit().catch((err) => {
  console.error("Audit error:", err);
  process.exit(1);
});
