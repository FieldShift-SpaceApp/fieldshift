// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SupportDisclaimer } from "@/components/trust/support-disclaimer";
import { t } from "@/i18n";

describe("<SupportDisclaimer>", () => {
  it("renders the FR7 notice as a note with the text from the strings file", () => {
    render(<SupportDisclaimer />);
    const note = screen.getByRole("note");
    expect(note.textContent).toBe(t("disclaimer.support"));
    expect(note.textContent).toContain("does not replace");
  });
});
