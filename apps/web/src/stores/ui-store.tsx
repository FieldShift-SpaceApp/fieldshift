// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// UI state only (architecture: State Management). One store per page, created from props, so the
// server render and the first client render agree (no hydration mismatch). Site data never enters
// the store. Concept-specific state (priorities, constraints) waits for the concept decision (C1).
"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import { createStore, useStore, type StoreApi } from "zustand";
import type { ProvenanceId, UnitSystem } from "@fieldshift/contracts";

export interface UiState {
  unitSystem: UnitSystem;
  provenance: { open: boolean; ids: ProvenanceId[] };
}

export interface UiActions {
  setUnitSystem: (unitSystem: UnitSystem) => void;
  openProvenance: (ids: ProvenanceId[]) => void;
  closeProvenance: () => void;
}

export type UiStore = UiState & UiActions;

export function createUiStore(init: Pick<UiState, "unitSystem">): StoreApi<UiStore> {
  return createStore<UiStore>()((set) => ({
    unitSystem: init.unitSystem,
    provenance: { open: false, ids: [] },
    setUnitSystem: (unitSystem) => set({ unitSystem }),
    openProvenance: (ids) => set({ provenance: { open: true, ids } }),
    closeProvenance: () => set({ provenance: { open: false, ids: [] } }),
  }));
}

const UiStoreContext = createContext<StoreApi<UiStore> | null>(null);

/** `unitSystem` is the site's default (FR23); each page gets a fresh store. */
export function UiStoreProvider({ unitSystem, children }: { unitSystem: UnitSystem; children: ReactNode }) {
  const [store] = useState(() => createUiStore({ unitSystem }));
  return <UiStoreContext.Provider value={store}>{children}</UiStoreContext.Provider>;
}

export function useUiStore<T>(selector: (s: UiStore) => T): T {
  const store = useContext(UiStoreContext);
  if (!store) throw new Error("useUiStore must be used inside <UiStoreProvider>");
  return useStore(store, selector);
}
