"""ADR-0037 Wave 6 pre-build test assertions.

Workstream A: Dashboard A11y (T-0037-001 through T-0037-026)
Workstream B: Product Spec Additions (T-0037-027 through T-0037-035)
Workstream C: Cursor Parity -- BLOCKED pending ADR-0035. Tests T-0037-036 through
T-0037-041 are NOT written here.

Test authoring contract (Retro Lesson #002):
  Tests assert what code SHOULD do per the ADR, not what it currently does.
  T-0037-001 through T-0037-022 are pre-build: they FAIL until Colby implements.
  T-0037-023 through T-0037-026 are regression guards: they PASS now against the
  current file and must continue to pass after Colby's changes.
  T-0037-027 through T-0037-035 are pre-build: they FAIL until Robert-spec writes.

Pre-existing const count baseline (T-0037-023):
  brain/ui/dashboard.html has exactly 3 existing `const` declarations at lines
  903, 904, and 911. Colby must not introduce additional `let` or `const`
  declarations. The regression guard asserts the total stays at or below 3.
"""

import re
from pathlib import Path

# ── Project root (this file lives at tests/test_adr0037_wave6.py) ─────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DASHBOARD_HTML = PROJECT_ROOT / "brain" / "ui" / "dashboard.html"

# Known pre-existing count of `let`/`const` declarations in the script block.
# Lines 903, 904, 911 of the unmodified file.
_EXISTING_LET_CONST_COUNT = 3


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _html() -> str:
    """Return the full text of dashboard.html."""
    return DASHBOARD_HTML.read_text()


def _extract_between(text: str, start_pattern: str, end_pattern: str) -> str:
    """Return the slice of text from the first match of start_pattern up to
    the first subsequent match of end_pattern. Returns empty string if either
    boundary is not found or end precedes start."""
    m_start = re.search(start_pattern, text)
    if not m_start:
        return ""
    tail = text[m_start.start():]
    m_end = re.search(end_pattern, tail)
    if not m_end:
        return tail
    return tail[: m_end.end()]


def _function_body(text: str, fn_name: str) -> str:
    """Extract the text from the opening of a JS function definition to the
    line before the next top-level `function` keyword (or end-of-script).

    Searches for `function <fn_name>` and captures until the next bare
    `function` keyword at the same indentation level, or end of text.
    This is a heuristic sufficient for these grep-style assertions.
    """
    start_pat = rf"function\s+{re.escape(fn_name)}\s*\("
    m = re.search(start_pat, text)
    if not m:
        return ""
    tail = text[m.start():]
    # Find next function keyword that is NOT inside this function.
    # Simple heuristic: find next `function ` that is NOT indented more than
    # the current function.  For these tests we just look for the next
    # `\nfunction ` (newline + function at column 0 or small indent = sibling).
    next_fn = re.search(r"\n\s{0,8}function\s+\w", tail[10:])
    if next_fn:
        return tail[: next_fn.start() + 10]
    return tail


# ─────────────────────────────────────────────────────────────────────────────
# Workstream A -- Dashboard A11y
# ─────────────────────────────────────────────────────────────────────────────

# ── Step A1: Modal ARIA semantics + focus management ──────────────────────


def test_T_0037_001_modal_has_role_dialog():
    """T-0037-001: #agent-modal element has role="dialog" attribute.

    Pre-build: FAILS until Colby adds the attribute (Change A1.1).
    """
    html = _html()
    # Find the line(s) containing id="agent-modal"
    matches = [ln for ln in html.splitlines() if 'id="agent-modal"' in ln]
    assert matches, 'No line containing id="agent-modal" found in dashboard.html'
    target_line = matches[0]
    assert 'role="dialog"' in target_line, (
        f'#agent-modal element is missing role="dialog". Found: {target_line.strip()}'
    )


def test_T_0037_002_modal_has_aria_modal_true():
    """T-0037-002: #agent-modal element has aria-modal="true" attribute.

    Pre-build: FAILS until Colby adds the attribute (Change A1.1).
    """
    html = _html()
    matches = [ln for ln in html.splitlines() if 'id="agent-modal"' in ln]
    assert matches, 'No line containing id="agent-modal" found in dashboard.html'
    target_line = matches[0]
    assert 'aria-modal="true"' in target_line, (
        f'#agent-modal element is missing aria-modal="true". Found: {target_line.strip()}'
    )


def test_T_0037_003_modal_has_aria_labelledby_modal_agent_name():
    """T-0037-003: #agent-modal element has aria-labelledby="modal-agent-name".

    Pre-build: FAILS until Colby adds the attribute (Change A1.1).
    """
    html = _html()
    matches = [ln for ln in html.splitlines() if 'id="agent-modal"' in ln]
    assert matches, 'No line containing id="agent-modal" found in dashboard.html'
    target_line = matches[0]
    assert 'aria-labelledby="modal-agent-name"' in target_line, (
        f'#agent-modal element is missing aria-labelledby="modal-agent-name". '
        f'Found: {target_line.strip()}'
    )


def test_T_0037_004_modal_loading_div_has_aria_live_polite():
    """T-0037-004: #modal-body stable parent has aria-live="polite".

    Accessibility requirement: Live region (aria-live) must be placed on a
    stable, persistent parent element, not on dynamically-replaced children.
    The .modal-loading div is dynamically replaced by innerHTML; it must NOT
    carry aria-live. Instead, the stable parent #modal-body carries aria-live,
    and all content changes within it (including .modal-loading replacement)
    are announced by the live region.

    Pre-build: FAILS until Colby moves aria-live from .modal-loading to #modal-body.
    Note: This checks the static HTML declaration. The dynamic modal-open path
    (openAgentModal bodyEl.innerHTML) is covered by T-0037-021.
    """
    html = _html()
    matches = [ln for ln in html.splitlines() if 'id="modal-body"' in ln]
    assert matches, 'No line containing id="modal-body" found in dashboard.html'
    # The stable parent container must carry aria-live for a11y
    target_line = matches[0]
    assert 'aria-live="polite"' in target_line, (
        f'#modal-body element is missing aria-live="polite". '
        f'Found: {target_line.strip()}'
    )


def test_T_0037_005_open_agent_modal_saves_trigger_element():
    """T-0037-005: openAgentModal() saves the trigger element via document.activeElement.

    Pre-build: FAILS until Colby adds focus-save logic (Change A1.3).
    """
    html = _html()
    body = _function_body(html, "openAgentModal")
    assert body, "Function openAgentModal not found in dashboard.html"
    assert "document.activeElement" in body, (
        "openAgentModal() does not save document.activeElement as the modal trigger. "
        "Expected: modalTrigger = document.activeElement (or equivalent)."
    )


def test_T_0037_006_open_agent_modal_focuses_close_button():
    """T-0037-006: openAgentModal() calls .focus() on the close button or first
    focusable element to move keyboard focus into the modal.

    Pre-build: FAILS until Colby adds the focus() call (Change A1.3).
    """
    html = _html()
    body = _function_body(html, "openAgentModal")
    assert body, "Function openAgentModal not found in dashboard.html"
    assert ".focus()" in body, (
        "openAgentModal() does not call .focus() to move focus into the modal. "
        "Expected a .focus() call after the modal becomes visible."
    )


def test_T_0037_007_close_agent_modal_restores_focus_to_trigger():
    """T-0037-007: closeAgentModal() restores focus to the trigger element via
    modalTrigger.focus().

    Pre-build: FAILS until Colby updates closeAgentModal() (Change A1.4).
    """
    html = _html()
    body = _function_body(html, "closeAgentModal")
    assert body, "Function closeAgentModal not found in dashboard.html"
    assert "modalTrigger" in body, (
        "closeAgentModal() does not reference modalTrigger. "
        "Expected: if (modalTrigger) { modalTrigger.focus(); modalTrigger = null; }"
    )
    assert ".focus()" in body, (
        "closeAgentModal() does not call .focus() to restore focus to trigger element."
    )


def test_T_0037_008_modal_key_handler_exists_handles_escape_and_tab():
    """T-0037-008: A function named modalKeyHandler exists and handles both
    "Escape" and "Tab" key events.

    Pre-build: FAILS until Colby adds the function (Change A1.4).
    """
    html = _html()
    assert "function modalKeyHandler" in html, (
        "Function modalKeyHandler not found in dashboard.html. "
        "Expected: function modalKeyHandler(e) { ... } per ADR-0037 Change A1.4."
    )
    body = _function_body(html, "modalKeyHandler")
    assert 'e.key === "Escape"' in body or "e.key === 'Escape'" in body, (
        'modalKeyHandler does not handle the "Escape" key.'
    )
    assert 'e.key === "Tab"' in body or "e.key === 'Tab'" in body, (
        'modalKeyHandler does not handle the "Tab" key.'
    )


def test_T_0037_009_modal_key_handler_handles_shift_tab_wrap():
    """T-0037-009: modalKeyHandler handles Shift+Tab backward wrap within modal.

    Pre-build: FAILS until Colby implements the focus trap (Change A1.4).
    """
    html = _html()
    assert "function modalKeyHandler" in html, (
        "Function modalKeyHandler not found in dashboard.html."
    )
    body = _function_body(html, "modalKeyHandler")
    assert "e.shiftKey" in body, (
        "modalKeyHandler does not check e.shiftKey for Shift+Tab backward wrap. "
        "Expected: if (e.shiftKey) { ... } branch within Tab handling."
    )


def test_T_0037_010_open_agent_modal_attaches_modal_key_handler():
    """T-0037-010: openAgentModal() attaches modalKeyHandler via
    addEventListener("keydown", modalKeyHandler).

    Pre-build: FAILS until Colby adds the listener attachment (Change A1.3).
    """
    html = _html()
    body = _function_body(html, "openAgentModal")
    assert body, "Function openAgentModal not found in dashboard.html"
    # Must wire the keydown listener to the overlay using modalKeyHandler by name
    assert 'addEventListener("keydown", modalKeyHandler)' in body or \
           "addEventListener('keydown', modalKeyHandler)" in body, (
        "openAgentModal() does not attach modalKeyHandler via "
        'addEventListener("keydown", modalKeyHandler). '
        "Focus trap will not activate when the modal opens."
    )


def test_T_0037_011_close_agent_modal_removes_modal_key_handler():
    """T-0037-011: closeAgentModal() removes modalKeyHandler via
    removeEventListener("keydown", modalKeyHandler).

    Pre-build: FAILS until Colby updates closeAgentModal() (Change A1.4).
    """
    html = _html()
    body = _function_body(html, "closeAgentModal")
    assert body, "Function closeAgentModal not found in dashboard.html"
    assert 'removeEventListener("keydown", modalKeyHandler)' in body or \
           "removeEventListener('keydown', modalKeyHandler)" in body, (
        "closeAgentModal() does not remove modalKeyHandler. "
        "The focus trap will leak after the modal closes."
    )


# ── Step A2: Agent card keyboard accessibility ────────────────────────────


def test_T_0037_012_render_agents_non_eva_cards_have_role_button():
    """T-0037-012: renderAgents() output includes role="button" for non-Eva cards.

    The return string must conditionally include role="button" for non-Eva cards.
    Pre-build: FAILS until Colby adds the conditional attribute (Change A2.2).
    """
    html = _html()
    # Locate the renderAgents function
    body = _function_body(html, "renderAgents")
    assert body, "Function renderAgents not found in dashboard.html"
    assert 'role="button"' in body, (
        'renderAgents() does not produce role="button" for agent cards. '
        "Expected: conditional role=\"button\" for non-Eva cards per ADR-0037 Change A2.2."
    )


def test_T_0037_013_render_agents_non_eva_cards_have_tabindex_0():
    """T-0037-013: renderAgents() output includes tabindex="0" for non-Eva cards.

    Pre-build: FAILS until Colby adds the conditional attribute (Change A2.2).
    """
    html = _html()
    body = _function_body(html, "renderAgents")
    assert body, "Function renderAgents not found in dashboard.html"
    assert 'tabindex="0"' in body, (
        'renderAgents() does not produce tabindex="0" for agent cards. '
        "Non-Eva agent cards must be reachable via Tab key."
    )


def test_T_0037_014_eva_card_excluded_from_role_button_and_tabindex():
    """T-0037-014: Eva orchestrator card does NOT receive role="button" or tabindex="0".

    The isEva conditional must exclude these attributes for Eva's card.
    Pre-build: FAILS until Colby implements the isEva guard (Change A2.2).
    """
    html = _html()
    body = _function_body(html, "renderAgents")
    assert body, "Function renderAgents not found in dashboard.html"
    # The conditional must gate on isEva.  Verify isEva is used as the guard.
    assert "isEva" in body, (
        "renderAgents() does not reference isEva variable. "
        "Eva's card must be excluded from role=button / tabindex=0."
    )
    # The expression must NOT give role="button" to all cards unconditionally.
    # Correct pattern: (isEva ? '' : ' role="button" tabindex="0"')
    # We verify role="button" appears in the same expression that checks isEva.
    # Extract the ternary/conditional containing isEva and confirm it produces
    # role="button" only for the non-Eva branch.
    iseva_context = re.search(r'isEva.{0,200}role="button"', body, re.DOTALL)
    assert iseva_context, (
        "renderAgents() does not guard role=\"button\" behind the isEva conditional. "
        "Eva's card must not receive role=button."
    )


def test_T_0037_015_agent_cards_have_keydown_listener_for_enter_and_space():
    """T-0037-015: Agent cards have a keydown event listener that handles Enter and Space.

    Pre-build: FAILS until Colby adds the keyboard handler (Change A2.3).
    """
    html = _html()
    # Check within the cards.forEach / renderAgents wiring section
    # Look for keydown addEventListener followed by Enter and Space checks
    assert 'addEventListener("keydown"' in html or "addEventListener('keydown'" in html, (
        "No keydown addEventListener found in dashboard.html. "
        "Agent cards must handle Enter and Space key presses."
    )
    # Find a keydown handler referencing both Enter and Space
    keydown_blocks = re.findall(
        r'addEventListener\(["\']keydown["\'].*?\}\s*\)',
        html,
        re.DOTALL,
    )
    found_enter_and_space = any(
        ('"Enter"' in b or "'Enter'" in b) and ('" "' in b or "' '" in b or '" "' in b)
        for b in keydown_blocks
    )
    assert found_enter_and_space, (
        'No keydown handler found that handles both "Enter" and " " (Space). '
        "Agent cards must respond to Enter and Space per WCAG 2.1 SC 2.1.1."
    )


def test_T_0037_016_space_keydown_calls_prevent_default():
    """T-0037-016: The card keydown handler calls e.preventDefault() for Space key.

    Prevents page scroll when Space activates a card.
    Pre-build: FAILS until Colby adds the preventDefault() call (Change A2.3).
    """
    html = _html()
    # Locate keydown listeners that reference Space and check for preventDefault
    keydown_region = _extract_between(
        html,
        r'addEventListener\(["\']keydown["\']',
        r'\}\s*\)',
    )
    assert "preventDefault" in keydown_region, (
        "Keydown handler for agent cards does not call e.preventDefault(). "
        "Space key will scroll the page instead of activating the card."
    )


def test_T_0037_017_agent_card_focus_visible_css_rule_exists():
    """T-0037-017: CSS contains a :focus-visible rule for .agent-card.

    Pre-build: FAILS until Colby adds the CSS rule (Change A2.1).
    """
    html = _html()
    # Match .agent-card:focus-visible selector
    assert re.search(r'\.agent-card:focus-visible', html), (
        "No .agent-card:focus-visible CSS rule found in dashboard.html. "
        "Agent cards must have a visible focus indicator for keyboard navigation "
        "per WCAG 2.1 SC 2.4.7."
    )


def test_T_0037_018_orchestrator_card_focus_visible_sets_outline_none():
    """T-0037-018: .agent-card--orchestrator:focus-visible sets outline: none.

    Eva's card is non-interactive and must not show a focus ring.
    Pre-build: FAILS until Colby adds the CSS rule (Change A2.1).
    """
    html = _html()
    # Find the orchestrator focus-visible rule
    match = re.search(
        r'\.agent-card--orchestrator:focus-visible\s*\{[^}]*\}',
        html,
        re.DOTALL,
    )
    assert match, (
        "No .agent-card--orchestrator:focus-visible CSS rule found in dashboard.html. "
        "Expected: .agent-card--orchestrator:focus-visible { outline: none; }"
    )
    rule_body = match.group(0)
    assert "outline" in rule_body and "none" in rule_body, (
        ".agent-card--orchestrator:focus-visible rule exists but does not set outline: none. "
        f"Found: {rule_body.strip()}"
    )


# ── Step A3: Loading states on async surfaces ─────────────────────────────


def test_T_0037_019_load_data_inserts_skeleton_html_before_promise_all():
    """T-0037-019: loadData() inserts skeleton HTML before the Promise.all() call.

    Pre-build: FAILS until Colby adds skeleton injection (Change A3.2).
    """
    html = _html()
    load_data_body = _function_body(html, "loadData")
    assert load_data_body, "Function loadData not found in dashboard.html"
    # Verify skeleton class appears in loadData and before Promise.all
    promise_all_pos = load_data_body.find("Promise.all")
    assert promise_all_pos > 0, "Promise.all not found in loadData() body"
    before_promise = load_data_body[:promise_all_pos]
    assert "skeleton" in before_promise, (
        "loadData() does not insert skeleton HTML before Promise.all(). "
        "Users see a blank page instead of a skeleton shimmer while loading."
    )


def test_T_0037_020_skeleton_guarded_by_empty_agent_data_check():
    """T-0037-020: Skeleton insertion in loadData() is guarded by a !agentData.length
    or equivalent check to prevent skeleton flash on auto-refresh.

    Pre-build: FAILS until Colby adds the guard (Change A3.2).
    """
    html = _html()
    load_data_body = _function_body(html, "loadData")
    assert load_data_body, "Function loadData not found in dashboard.html"
    # Look for the guard: !agentData.length or agentData.length === 0 or similar
    has_guard = bool(
        re.search(r'!\s*agentData\.length', load_data_body) or
        re.search(r'agentData\.length\s*===?\s*0', load_data_body) or
        re.search(r'agentData\.length\s*<\s*1', load_data_body)
    )
    assert has_guard, (
        "loadData() skeleton insertion is not guarded against re-render. "
        "Expected: !agentData.length or equivalent check before injecting skeletons. "
        "Without the guard, skeletons flash on every auto-refresh interval."
    )


def test_T_0037_021_modal_loading_uses_skeleton_class_not_plain_text():
    """T-0037-021: openAgentModal() sets bodyEl.innerHTML to skeleton shimmer HTML,
    not plain text "Loading agent detail...".

    Pre-build: FAILS until Colby replaces plain text with skeleton (Change A3.4).
    """
    html = _html()
    body = _function_body(html, "openAgentModal")
    assert body, "Function openAgentModal not found in dashboard.html"
    # Find the bodyEl.innerHTML assignment
    inner_html_assignments = re.findall(
        r'bodyEl\.innerHTML\s*=\s*["\'].*?["\']',
        body,
        re.DOTALL,
    )
    # Also capture multi-line string concatenation patterns
    loading_section = _extract_between(
        body,
        r'bodyEl\.innerHTML',
        r';',
    )
    assert "skeleton" in loading_section, (
        "openAgentModal() bodyEl.innerHTML does not use skeleton class. "
        'Expected: skeleton shimmer HTML instead of plain text "Loading agent detail...". '
        f"Found: {loading_section[:200].strip()}"
    )


def test_T_0037_022_scope_selector_has_aria_live_polite():
    """T-0037-022: The scope selector container (#scope-selector) has aria-live="polite".

    Pre-build: FAILS until Colby adds the attribute to the HTML element (Change A3.3).
    """
    html = _html()
    matches = [ln for ln in html.splitlines() if 'id="scope-selector"' in ln]
    assert matches, 'No element with id="scope-selector" found in dashboard.html'
    target_line = matches[0]
    assert "aria-live" in target_line, (
        f'#scope-selector element is missing aria-live attribute. '
        f'Found: {target_line.strip()}'
    )


# ── Regression guards (should PASS against current file) ─────────────────


def test_T_0037_023_no_new_let_const_declarations_introduced():
    """T-0037-023 (regression guard): Colby must not introduce new let/const
    declarations. The file has exactly 3 pre-existing const declarations
    (lines 903, 904, 911). The count must remain at or below that baseline.

    Should currently PASS. Fails if Colby adds let/const (ES5 compat rule).
    """
    html = _html()
    # Count all let/const declarations at the start of a line (with any indentation)
    matches = re.findall(r'^\s*(let|const)\s', html, re.MULTILINE)
    assert len(matches) <= _EXISTING_LET_CONST_COUNT, (
        f"New let/const declarations detected. "
        f"Baseline: {_EXISTING_LET_CONST_COUNT}, current count: {len(matches)}. "
        "dashboard.html targets ES5 compatibility -- use var for new declarations."
    )


def test_T_0037_024_document_level_escape_handler_still_present():
    """T-0037-024 (regression guard): document.addEventListener("keydown") with
    Escape check still exists as defense-in-depth (ADR-0037 Change A1.4 note).

    Should currently PASS. Fails if Colby removes it.
    """
    html = _html()
    # The document-level handler must still exist outside modalKeyHandler
    # We look for document.addEventListener("keydown" in the HTML
    assert 'document.addEventListener("keydown"' in html or \
           "document.addEventListener('keydown'" in html, (
        "document.addEventListener keydown handler was removed from dashboard.html. "
        "ADR-0037 requires it to remain as defense-in-depth for Escape key close."
    )
    # Additionally verify it still handles Escape
    doc_handler_region = _extract_between(
        html,
        r'document\.addEventListener\(["\']keydown',
        r'\}\s*\)',
    )
    assert "Escape" in doc_handler_region, (
        'document-level keydown handler no longer checks for "Escape" key. '
        "This is a regression -- the handler must remain as defense-in-depth."
    )


def test_T_0037_025_click_outside_close_handler_still_present():
    """T-0037-025 (regression guard): Click-outside modal-close handler still
    registered on #agent-modal-overlay.

    Should currently PASS. Fails if Colby removes it.
    """
    html = _html()
    assert 'getElementById("agent-modal-overlay")' in html or \
           "getElementById('agent-modal-overlay')" in html, (
        "agent-modal-overlay getElementById reference missing from dashboard.html."
    )
    # Verify overlay click handler wires to closeAgentModal
    overlay_section = _extract_between(
        html,
        r'getElementById\(["\']agent-modal-overlay["\'].*?addEventListener',
        r'\}\s*\)',
    )
    assert "closeAgentModal" in overlay_section, (
        "Click-outside handler on #agent-modal-overlay no longer calls closeAgentModal. "
        "This is a regression -- mouse users must still be able to close the modal."
    )


def test_T_0037_026_escape_html_still_wraps_inner_html_assignments():
    """T-0037-026 (regression guard): escapeHtml() is still used to wrap innerHTML
    assignments (XSS guard from Wave 3 / ADR-0034).

    Should currently PASS. Fails if Colby removes escapeHtml() calls.
    """
    html = _html()
    assert "escapeHtml(" in html, (
        "escapeHtml() function calls not found in dashboard.html. "
        "This is a regression -- Wave 3 XSS guard must remain intact."
    )
    # Count innerHTML assignments that use escapeHtml to confirm the guard is active
    escaped_assignments = re.findall(r'innerHTML.*?escapeHtml\(', html, re.DOTALL)
    assert len(escaped_assignments) >= 1, (
        "No innerHTML assignment uses escapeHtml(). "
        "XSS guard appears to have been removed or bypassed."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Workstream B -- Product Spec Additions
# ─────────────────────────────────────────────────────────────────────────────

# Spec file paths
_SPEC_OBSERVATION_MASKING = PROJECT_ROOT / "docs" / "product" / "observation-masking.md"
_SPEC_TOKEN_BUDGET = PROJECT_ROOT / "docs" / "product" / "token-budget-estimate-gate.md"
_SPEC_STOP_REASON = PROJECT_ROOT / "docs" / "product" / "named-stop-reason-taxonomy.md"
_SPEC_AGENT_DISCOVERY = PROJECT_ROOT / "docs" / "product" / "agent-discovery.md"
_SPEC_TEAM_ADDENDUM = PROJECT_ROOT / "docs" / "product" / "team-collaboration-enhancements-addendum.md"

_ALL_SPECS = [
    _SPEC_OBSERVATION_MASKING,
    _SPEC_TOKEN_BUDGET,
    _SPEC_STOP_REASON,
    _SPEC_AGENT_DISCOVERY,
    _SPEC_TEAM_ADDENDUM,
]

# Required section headings per the established product spec format
# (established by docs/product/dashboard-integration.md and agent-telemetry.md)
_REQUIRED_HEADINGS = [
    r"##\s+.*(DoR|Requirement)",   # DoR table
    r"##\s+.*(Problem|The Problem)",
    r"##\s+.*(Persona|User|Who Is This For)",
    r"##\s+.*(Acceptance Criteria|Acceptance)",
]


def _spec_has_format_markers(path: Path) -> tuple[bool, list[str]]:
    """Return (all_present, missing_headings) for a spec file."""
    content = path.read_text()
    missing = []
    for pattern in _REQUIRED_HEADINGS:
        if not re.search(pattern, content, re.IGNORECASE):
            missing.append(pattern)
    return len(missing) == 0, missing


# ── T-0037-027 through T-0037-031: Spec existence ─────────────────────────


def test_T_0037_027_observation_masking_spec_exists():
    """T-0037-027: docs/product/observation-masking.md exists with spec format markers.

    Pre-build: FAILS until Robert-spec writes the file (ADR-0037 Step B1 file 1).
    """
    assert _SPEC_OBSERVATION_MASKING.exists(), (
        f"Missing spec file: {_SPEC_OBSERVATION_MASKING}. "
        "Robert-spec must write the observation-masking product spec (ADR-0011)."
    )
    content = _SPEC_OBSERVATION_MASKING.read_text()
    assert "## " in content, (
        "observation-masking.md exists but has no section headings -- likely empty."
    )
    # Must contain at minimum an Acceptance Criteria section
    assert re.search(r"##.*Acceptance", content, re.IGNORECASE), (
        "observation-masking.md is missing an Acceptance Criteria section."
    )


def test_T_0037_028_token_budget_estimate_gate_spec_exists():
    """T-0037-028: docs/product/token-budget-estimate-gate.md exists with spec format markers.

    Pre-build: FAILS until Robert-spec writes the file (ADR-0037 Step B1 file 2).
    """
    assert _SPEC_TOKEN_BUDGET.exists(), (
        f"Missing spec file: {_SPEC_TOKEN_BUDGET}. "
        "Robert-spec must write the token-budget-estimate-gate product spec (ADR-0029)."
    )
    content = _SPEC_TOKEN_BUDGET.read_text()
    assert re.search(r"##.*Acceptance", content, re.IGNORECASE), (
        "token-budget-estimate-gate.md is missing an Acceptance Criteria section."
    )


def test_T_0037_029_named_stop_reason_taxonomy_spec_exists():
    """T-0037-029: docs/product/named-stop-reason-taxonomy.md exists with spec format markers.

    Pre-build: FAILS until Robert-spec writes the file (ADR-0037 Step B1 file 3).
    """
    assert _SPEC_STOP_REASON.exists(), (
        f"Missing spec file: {_SPEC_STOP_REASON}. "
        "Robert-spec must write the named-stop-reason-taxonomy product spec (ADR-0028)."
    )
    content = _SPEC_STOP_REASON.read_text()
    assert re.search(r"##.*Acceptance", content, re.IGNORECASE), (
        "named-stop-reason-taxonomy.md is missing an Acceptance Criteria section."
    )


def test_T_0037_030_agent_discovery_spec_exists():
    """T-0037-030: docs/product/agent-discovery.md exists with spec format markers.

    Pre-build: FAILS until Robert-spec writes the file (ADR-0037 Step B1 file 4).
    """
    assert _SPEC_AGENT_DISCOVERY.exists(), (
        f"Missing spec file: {_SPEC_AGENT_DISCOVERY}. "
        "Robert-spec must write the agent-discovery product spec (ADR-0008)."
    )
    content = _SPEC_AGENT_DISCOVERY.read_text()
    assert re.search(r"##.*Acceptance", content, re.IGNORECASE), (
        "agent-discovery.md is missing an Acceptance Criteria section."
    )


def test_T_0037_031_team_collab_addendum_exists_and_references_base_spec():
    """T-0037-031: docs/product/team-collaboration-enhancements-addendum.md exists
    and references the base team-collaboration-enhancements.md spec.

    Pre-build: FAILS until Robert-spec writes the file (ADR-0037 Step B1 file 5).
    """
    assert _SPEC_TEAM_ADDENDUM.exists(), (
        f"Missing spec file: {_SPEC_TEAM_ADDENDUM}. "
        "Robert-spec must write the team-collaboration addendum (S6/S7 coverage)."
    )
    content = _SPEC_TEAM_ADDENDUM.read_text()
    # Must reference the base spec
    assert "team-collaboration-enhancements" in content, (
        "team-collaboration-enhancements-addendum.md does not reference the base spec "
        "(team-collaboration-enhancements.md). "
        "ADR-0037 requires the addendum to explicitly reference the base document."
    )


# ── T-0037-032: Format compliance for all 5 specs ─────────────────────────


def test_T_0037_032_all_five_specs_follow_established_format():
    """T-0037-032: Each of the 5 new product specs follows the established format:
    DoR table, Problem section, Personas section, Acceptance Criteria section.

    Pre-build: FAILS until Robert-spec writes all 5 files with correct structure.
    """
    failures = []
    for spec_path in _ALL_SPECS:
        if not spec_path.exists():
            failures.append(f"{spec_path.name}: FILE DOES NOT EXIST")
            continue
        all_present, missing = _spec_has_format_markers(spec_path)
        if not all_present:
            failures.append(
                f"{spec_path.name}: missing sections matching: {missing}"
            )
    assert not failures, (
        "Product spec format violations found:\n" +
        "\n".join(f"  - {f}" for f in failures)
    )


# ── T-0037-033/034: S6 and S7 coverage in the addendum ────────────────────


def test_T_0037_033_addendum_covers_handoff_brief_protocol():
    """T-0037-033: team-collaboration-enhancements-addendum.md contains acceptance
    criteria covering the Handoff Brief protocol (S6).

    Pre-build: FAILS until Robert-spec writes the S6 acceptance criteria.
    """
    assert _SPEC_TEAM_ADDENDUM.exists(), (
        f"Missing spec file: {_SPEC_TEAM_ADDENDUM}."
    )
    content = _SPEC_TEAM_ADDENDUM.read_text()
    has_handoff = bool(
        re.search(r'handoff.brief', content, re.IGNORECASE) or
        re.search(r'handoff\s+brief', content, re.IGNORECASE)
    )
    assert has_handoff, (
        "team-collaboration-enhancements-addendum.md does not contain Handoff Brief "
        "content (S6 from ADR-0037). "
        "Expected acceptance criteria covering the Handoff Brief protocol."
    )


def test_T_0037_034_addendum_covers_context_brief_dual_write_gate():
    """T-0037-034: team-collaboration-enhancements-addendum.md contains acceptance
    criteria covering the context-brief dual-write gate (S7).

    Pre-build: FAILS until Robert-spec writes the S7 acceptance criteria.
    """
    assert _SPEC_TEAM_ADDENDUM.exists(), (
        f"Missing spec file: {_SPEC_TEAM_ADDENDUM}."
    )
    content = _SPEC_TEAM_ADDENDUM.read_text()
    has_dual_write = bool(
        re.search(r'context.brief', content, re.IGNORECASE) or
        re.search(r'dual.write', content, re.IGNORECASE)
    )
    assert has_dual_write, (
        "team-collaboration-enhancements-addendum.md does not contain context-brief "
        "dual-write gate content (S7 from ADR-0037). "
        "Expected acceptance criteria covering the dual-write gate."
    )


# ── T-0037-035: Testability of acceptance criteria ────────────────────────


def test_T_0037_035_all_spec_acceptance_criteria_are_verifiable():
    """T-0037-035: Each acceptance criterion across all 5 specs is phrased as a
    verifiable assertion using action verbs: MUST, SHOULD, returns, produces,
    displays, blocks, emits, or equivalent.

    Pre-build: FAILS until Robert-spec writes the files with proper AC phrasing.
    """
    # Action verbs that indicate a testable assertion
    action_verb_pattern = re.compile(
        r'\b(MUST|SHOULD|SHALL|returns?|produces?|displays?|blocks?|'
        r'emits?|shows?|writes?|creates?|prevents?|fails?|succeeds?|'
        r'contains?|exists?|does not|is not|are not)\b',
        re.IGNORECASE,
    )
    failures = []
    for spec_path in _ALL_SPECS:
        if not spec_path.exists():
            failures.append(f"{spec_path.name}: FILE DOES NOT EXIST")
            continue
        content = spec_path.read_text()
        # Extract content under the Acceptance Criteria section
        ac_section = _extract_between(
            content,
            r"##.*Acceptance Criteria",
            r"\n##\s+",
        )
        if not ac_section:
            failures.append(
                f"{spec_path.name}: Acceptance Criteria section is empty or missing"
            )
            continue
        # Count lines that look like AC items (bullet or numbered)
        ac_lines = [
            ln for ln in ac_section.splitlines()
            # Exclude: bold subheadings (**text**:), HR separators (---/***),
            # sub-indented example/illustration bullets (2+ spaces before -),
            # and blank lines. Only keep top-level AC items.
            if re.match(r'^[-*]|^ [-*]|^\d+\.', ln)  # top-level bullet or numbered
            and not re.match(r'^\s*\*\*', ln)          # skip **bold subheadings**
            and not re.match(r'^\s*---', ln)            # skip --- separators
            and not re.match(r'^\s*\*\*\*', ln)       # skip *** horizontal rules
            and not re.match(r'^  +[-*]', ln)           # skip sub-indented examples
        ]
        if not ac_lines:
            failures.append(
                f"{spec_path.name}: No bullet/numbered acceptance criteria found"
            )
            continue
        # Each AC line should contain at least one action verb
        non_testable = [
            ln.strip() for ln in ac_lines
            if not action_verb_pattern.search(ln)
        ]
        if non_testable:
            failures.append(
                f"{spec_path.name}: {len(non_testable)} acceptance criteria lack "
                f"action verbs (MUST/SHOULD/returns/etc): "
                + "; ".join(non_testable[:3])  # first 3 for brevity
            )
    assert not failures, (
        "Acceptance criteria testability violations:\n" +
        "\n".join(f"  - {f}" for f in failures)
    )
