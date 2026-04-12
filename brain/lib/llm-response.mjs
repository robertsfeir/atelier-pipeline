/**
 * LLM response null guard helper.
 * ADR-0034 Wave 3 Step 3.5
 *
 * Single source of truth for safely extracting `choices[0].message.content`
 * from an LLM (OpenRouter / OpenAI) chat-completion response. Centralizes the
 * defensive null/shape checks so callers cannot crash on malformed responses.
 *
 * Pre-fix (S10 bug): both conflict.mjs and consolidation.mjs accessed
 *   data.choices[0].message.content
 * directly. A null `data`, an empty `choices` array, a missing `message`, or
 * a null `content` would throw an unhandled TypeError that crashed the
 * consolidation/conflict cycle.
 *
 * Post-fix: every caller imports `assertLlmContent` from this module and the
 * direct `.choices[0].message.content` access pattern only exists here.
 */

/**
 * Returns the LLM response content string if the payload is well-formed.
 * Throws a named Error otherwise.
 *
 * @param {*} data - The parsed JSON body of an LLM chat-completion response.
 * @param {string} context - Short label identifying the caller (e.g. 'conflict',
 *   'consolidation') -- included in the error message to aid debugging.
 * @returns {string} The non-empty content string from `data.choices[0].message.content`.
 * @throws {Error} If `data` is null/undefined, `choices` is missing/empty,
 *   `message` is missing, or `content` is null/undefined/empty. The error
 *   message contains "malformed" so log consumers can pattern-match it, plus
 *   a truncated dump of the payload (first 200 chars of JSON.stringify).
 */
export function assertLlmContent(data, context) {
  const ctx = context || 'unknown';
  let dump;
  try {
    dump = JSON.stringify(data);
  } catch {
    dump = String(data);
  }
  const truncated = dump.slice(0, 200);

  if (data == null) {
    throw new Error(`LLM response malformed (${ctx}): ${truncated}`);
  }
  if (!Array.isArray(data.choices) || data.choices.length === 0) {
    throw new Error(`LLM response malformed (${ctx}): ${truncated}`);
  }
  const first = data.choices[0];
  if (first == null || first.message == null) {
    throw new Error(`LLM response malformed (${ctx}): ${truncated}`);
  }
  const content = first.message.content;
  if (content == null || content === '') {
    throw new Error(`LLM response malformed (${ctx}): ${truncated}`);
  }
  return content;
}
