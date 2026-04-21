"""ADR-0042 baseline fixtures -- Step 0 snapshot.

Captured before any ADR-0042 edits land (pre-build state).  All
"byte-identical to pre-ADR-0042 state" tests (T-0042-019, T-0042-029,
T-0042-035, T-0042-042) reference this module as the authoritative source.

Hashing algorithm: SHA-256 over UTF-8 encoded file content.
Structural hashes (CHANGED_AGENT_STRUCTURAL_HASHES): model: and effort:
lines stripped before hashing -- so the hash covers everything EXCEPT those
two fields.  Unchanged-agent hashes (UNCHANGED_AGENT_FULL_HASHES): full
content hashed verbatim.

Git blob hashes: produced by `git hash-object <file>` at snapshot time.
"""

# ---------------------------------------------------------------------------
# T-0042-029: enforce-scout-swarm.sh must be byte-identical to this.
# Captured: git hash-object source/claude/hooks/enforce-scout-swarm.sh
# ---------------------------------------------------------------------------
HOOK_BLOB_HASH = "f662a0e7bbdc84325698ef2a00999e9231062cd4"

# ---------------------------------------------------------------------------
# T-0042-035: ADR-0041 file must be byte-identical to this (immutability).
# Captured: git hash-object docs/architecture/ADR-0041-effort-per-agent-map.md
# ---------------------------------------------------------------------------
ADR_0041_BLOB_HASH = "6a76bbab8a687923681c1304601e6aa07647f9d4"

# ---------------------------------------------------------------------------
# T-0042-042: MDC wrapper snapshot.
# The first two ---...--- frontmatter blocks in
# .cursor-plugin/rules/pipeline-models.mdc must remain byte-identical.
# This is the 9-line wrapper (182 bytes) preceding the body.
# ---------------------------------------------------------------------------
MDC_WRAPPER_SNAPSHOT = (
    "---\n"
    "description: Pipeline model assignment tables -- loaded when working with pipeline state\n"
    "alwaysApply: false\n"
    'globs: ["docs/pipeline/**"]\n'
    "---\n"
    "---\n"
    "paths:\n"
    '  - "docs/pipeline/**"\n'
    "---\n"
)

# ---------------------------------------------------------------------------
# T-0042-019: Structural hashes for CHANGED agents (8 agents x 2 platforms).
# model: and effort: lines stripped before hashing.
# Verifies no non-model/effort fields were modified during the ADR-0042 edits.
# ---------------------------------------------------------------------------
CHANGED_AGENT_STRUCTURAL_HASHES: dict[str, dict[str, str]] = {
    # Updated 2026-04-20: baseline refreshed after commit 1cda942 bumped maxTurns 15->50.
    "roz": {
        "claude": "c4ab9a22f5a08c9579db7ed3d69a57002c85ae9cd9ae5dd9dfadaa2cf9866b34",
        "cursor": "298e317e4157f37f06446d53994af6be49ec673530a3d65dff5a27fe303d617c",
    },
    "robert": {
        "claude": "fcb2c32933ceec272d881af7109e8d0da445fbb5bcbe564d5a5b2819cd67b1db",
        "cursor": "fd309767bb3806f009518cfcfa5e57ed8b94ce7f771bae4e4ac6c17f374ba09a",
    },
    "sable": {
        "claude": "4d971bfe481ba5de6003c9a1db7684d54a9ef4187b0248f57b087a7942e44210",
        "cursor": "6382c1a4f6b29d41b96a569c519e510c76c28412818c6ca472345fa974649c18",
    },
    "sentinel": {
        "claude": "cc204be45a0b9d57df2a073d0a413e8b4c17bb53df75d6d0e5ec33651a4b3da7",
        "cursor": "0c77149f4a6ac5583f9ddb0686e265694a09edd5cca2a0dfbb406e99f6932735",
    },
    "deps": {
        "claude": "1e5cacdff8ea57265bcf2101b830d66ba939c9665e871f962c31a1290b3a74a5",
        "cursor": "2b970245fd22e1c25dfe10cb77ef9de65c05e75664e265c4e7ebfba7123125e8",
    },
    "ellis": {
        "claude": "1e1f1d014e960435917fec6cd5f4ac148d0d14657b152bf4254b054f6af92817",
        "cursor": "0596b8b3ff29380146ff8bd3771eed9d58001bdf1a04c5198ec520fbb86d3b1d",
    },
    "distillator": {
        "claude": "4595de0740c68d49efe377a09dd8b92ba01946fb168a5c13be67f658b3f00944",
        "cursor": "d4d83c0d3ab4bd2eb0d8ff0a1ac993bc45b370d4ef4dd9afac14a94ecb2b3cb4",
    },
    "brain-extractor": {
        "claude": "47c51a6eb196681286fef9764af3bd0f325d71c61be6644c746c41b2e99a2003",
        "cursor": "35541db88ab813a433ad9a28562c2c24d5916c5b76ba7bba4a91c986bf9e1a30",
    },
}

# ---------------------------------------------------------------------------
# UNCHANGED agents: full content hashes (both platforms).
# These agents must not be modified by ADR-0042 at all.
# ---------------------------------------------------------------------------
UNCHANGED_AGENT_FULL_HASHES: dict[str, dict[str, str]] = {
    "cal": {
        "claude": "8bda990d44c09f22621993def9999b699d815dbf2a10993c23bff9d4d79c555a",
        "cursor": "7c95d279448a274ae244ff48aaa142cee65532977a2e4fa66f8446bc4158fbbb",
    },
    "colby": {
        "claude": "219d6b34d0a27f538a678667b7e53e8a0f90be494157a5b44993c47d60ca3940",
        "cursor": "2230b3c813539a2e6b2d3ddae24d57ce9537c30318c7f8da6d3868b4bf79f71c",
    },
    "investigator": {
        "claude": "900056a5517b83b9400333e87f0ad04b950c4b0c1f5da9d5a3be235612124a72",
        "cursor": "eca912943daafb333f1c21ea4095eea1ae856698379600c7d972f67c4ddf4e0f",
    },
    "darwin": {
        "claude": "28faf16f0c663646b2ccb0548fc7f8c401a2ae99575bf2709e75bfcdee4c2530",
        "cursor": "385d0e3a32bf24b61773559c863407bea01a163e56f15f44d142655d5bbce13f",
    },
    "robert-spec": {
        "claude": "90cc17807493627c28dde4e7205a69935cdb125d7794b20b1434f3e5875d1c87",
        "cursor": "986bea8e2fc993a75a35eddeef539a457ddd9f14c0ba359e88bfc2613e2de119",
    },
    "sable-ux": {
        "claude": "f618b9e36fdadf4f09fab0076f9ecf1b76baa1782a8c4149ac1ccc1114852fb6",
        "cursor": "204fbed609ce461268f015b966e13d0c50110ea4ba6ce621ba2ce74c452cddb7",
    },
    "agatha": {
        "claude": "77c714a4b8690d53b548e9431cfc97a47c10375e040847a73a34dd3d20152f69",
        "cursor": "465dc314b32749f9ff53269441517174734615e16c12f4c838b4223d79520255",
    },
}

# ---------------------------------------------------------------------------
# T-0042-017: Unchanged-agent expected values (model + effort).
# ---------------------------------------------------------------------------
UNCHANGED_AGENT_EXPECTED: dict[str, dict[str, str]] = {
    "cal":          {"model": "opus",  "effort": "xhigh"},
    "colby":        {"model": "opus",  "effort": "high"},
    "investigator": {"model": "opus",  "effort": "high"},
    "darwin":       {"model": "opus",  "effort": "high"},
    "robert-spec":  {"model": "opus",  "effort": "medium"},
    "sable-ux":     {"model": "opus",  "effort": "medium"},
    "agatha":       {"model": "opus",  "effort": "medium"},
}

# ---------------------------------------------------------------------------
# T-0042-008 through T-0042-015: Changed-agent target values.
# ---------------------------------------------------------------------------
CHANGED_AGENT_EXPECTED: dict[str, dict[str, str]] = {
    "roz":             {"model": "opus",   "effort": "medium"},
    "robert":          {"model": "sonnet", "effort": "medium"},
    "sable":           {"model": "sonnet", "effort": "medium"},
    "sentinel":        {"model": "opus",   "effort": "low"},
    "deps":            {"model": "sonnet", "effort": "medium"},
    "ellis":           {"model": "sonnet", "effort": "low"},
    "distillator":     {"model": "sonnet", "effort": "low"},
    "brain-extractor": {"model": "sonnet", "effort": "low"},
}
