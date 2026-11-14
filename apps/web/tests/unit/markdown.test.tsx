// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Markdown } from "@/components/content/markdown";
import { REPO_BLOB_URL } from "@/lib/content";

afterEach(cleanup);

describe("<Markdown>", () => {
  it("drops raw HTML, rewrites relative links and shifts headings", () => {
    const { container } = render(
      <Markdown source="RESOURCES.md" headingOffset={1}>
        {"<!-- SI-assisted: hidden -->\n\n## Datasets\n\nSee [the log](SI-USAGE.md) and <b>bold</b>.\n"}
      </Markdown>,
    );
    expect(container.textContent).not.toContain("SI-assisted");
    expect(container.innerHTML).not.toContain("<b>");
    expect(screen.getByRole("heading", { level: 3, name: "Datasets" })).toBeTruthy();
    const link = screen.getByRole("link", { name: /the log/ });
    expect(link.getAttribute("href")).toBe(`${REPO_BLOB_URL}SI-USAGE.md`);
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("renders GFM tables inside a scroll container", () => {
    const { container } = render(<Markdown source="x.md">{"| a | b |\n|---|---|\n| 1 | 2 |\n"}</Markdown>);
    expect(container.querySelector("div.overflow-x-auto > table")).not.toBeNull();
  });

  it("does not render unsafe link schemes as links", () => {
    render(<Markdown source="x.md">{"[click](javascript:alert(1))"}</Markdown>);
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByText("click")).toBeTruthy();
  });
});
