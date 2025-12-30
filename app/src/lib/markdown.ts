/**
 * Escape HTML special characters to prevent XSS when using @html
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Process basic inline markdown for bold, italics, and code.
 * Supports:
 * - **bold** or __bold__ -> <strong>bold</strong>
 * - *italics* or _italics_ -> <em>italics</em>
 * - `code` -> <code>code</code>
 *
 * The input is HTML-escaped before markdown processing to prevent XSS.
 */
export function formatInlineMarkdown(text: string): string {
  let result = escapeHtml(text);

  // Process inline code first (`code`)
  result = result.replace(/`(.+?)`/g, '<code>$1</code>');

  // Process bold (**text** or __text__)
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  result = result.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Then process italics (*text* or _text_)
  result = result.replace(/\*(.+?)\*/g, '<em>$1</em>');
  result = result.replace(/_(.+?)_/g, '<em>$1</em>');

  return result;
}
