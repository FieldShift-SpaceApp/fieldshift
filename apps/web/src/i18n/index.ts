import { en, type MessageKey } from "./en";

export function t(key: MessageKey): string {
  return en[key];
}

export type { MessageKey };
