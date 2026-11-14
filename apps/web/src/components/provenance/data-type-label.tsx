// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// FR9: the data type is always visible next to the value. Text label, never color alone (PRD §3).
import type { DataType } from "@fieldshift/contracts";
import { t, type MessageKey } from "@/i18n";

function labelKey(dataType: DataType): MessageKey {
  switch (dataType) {
    case "satellite_observed":
      return "dataType.satellite_observed";
    case "modeled":
      return "dataType.modeled";
    case "computed":
      return "dataType.computed";
    case "user_provided":
      return "dataType.user_provided";
    default:
      return "dataType.unknown";
  }
}

export function DataTypeLabel({ dataType }: { dataType: DataType }) {
  return (
    <span data-data-type={dataType} className="text-xs text-muted-foreground">
      {t(labelKey(dataType))}
    </span>
  );
}
