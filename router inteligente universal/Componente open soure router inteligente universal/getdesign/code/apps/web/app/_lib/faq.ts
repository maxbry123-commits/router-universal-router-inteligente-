import { SITE_RUN_COST_DESCRIPTION } from "./site";

// Keep the visible answers and structured data in sync.
export const HOME_FAQ = [
  {
    question: "What is getdesign?",
    answer:
      "getdesign extracts a design system from a public website. It reads the site's CSS and captures the rendered page, then writes its colors, typography, spacing, and components to a design.md file.",
  },
  {
    question: "What is a design.md file?",
    answer:
      "A design.md is a Markdown document describing a website's design system. You can read it as a style guide or give it to a coding agent as context when building an interface. Visual runs also include captured screenshots.",
  },
  {
    question: "How do I extract a website's colors and fonts?",
    answer:
      "Save your Daytona and OpenAI keys in Account, then paste a public website URL into Agent. getdesign reads CSS tokens, captures the page in a browser, and generates a design document you can download. You can also explore cached examples without running providers.",
  },
  {
    question: "Can I use getdesign with a coding agent?",
    answer:
      "Yes. Give your coding agent the generated design.md and its screenshots, or install the getdesign Skill to extract design context using the agent's own tools. The CLI and TypeScript SDK also run locally on Bun, and the HTTP API supports hosted runs.",
  },
  {
    question: "Is there authentication or a paid tier?",
    answer:
      `The dashboard uses WorkOS sign-in. Hosted runs require your own Daytona and OpenAI keys; there is no getdesign API key in V1. ${SITE_RUN_COST_DESCRIPTION}`,
  },
  {
    question: "Are my design runs public?",
    answer:
      "Your dashboard runs are private until you publish them. Publishing creates a link that anyone can use to view and download the design document and screenshots. You can make a run private again to close future access; copies already downloaded remain with their recipients.",
  },
] as const;
