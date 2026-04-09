/**
 * brain/lib/hydrate.mjs
 *
 * Shared hydration functions re-exported from brain/scripts/hydrate-telemetry.mjs.
 * Used by the atelier_hydrate MCP tool (brain/lib/tools.mjs) so it can share
 * the same implementation that the standalone CLI script uses — without opening
 * a new DB connection.
 *
 * All logic lives in hydrate-telemetry.mjs. This module is a pure re-export
 * bridge. The main() guard in hydrate-telemetry.mjs prevents the CLI entry
 * point from running on import.
 */

export {
  expandHome,
  discoverEvaFiles,
  discoverSubagentFiles,
  alreadyHydrated,
  hydrateSubagentFile,
  hydrateEvaFile,
  insertTelemetryThought,
  generateTier3Summaries,
  parseStateFiles,
  parseJsonl,
  computeCost,
  lookupPricing,
  warnIfDefaultScope,
  stateItemAlreadyHydrated,
} from "../scripts/hydrate-telemetry.mjs";
