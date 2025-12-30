import { describe, it, expect } from 'vitest';
import { formatInlineMarkdown } from './markdown';

describe('formatInlineMarkdown', () => {
  describe('bold formatting', () => {
    it('converts **text** to <strong>text</strong>', () => {
      expect(formatInlineMarkdown('This is **bold** text')).toBe(
        'This is <strong>bold</strong> text',
      );
    });

    it('converts __text__ to <strong>text</strong>', () => {
      expect(formatInlineMarkdown('This is __bold__ text')).toBe(
        'This is <strong>bold</strong> text',
      );
    });

    it('handles multiple bold sections', () => {
      expect(formatInlineMarkdown('**first** and **second**')).toBe(
        '<strong>first</strong> and <strong>second</strong>',
      );
    });
  });

  describe('italic formatting', () => {
    it('converts *text* to <em>text</em>', () => {
      expect(formatInlineMarkdown('This is *italic* text')).toBe('This is <em>italic</em> text');
    });

    it('converts _text_ to <em>text</em>', () => {
      expect(formatInlineMarkdown('This is _italic_ text')).toBe('This is <em>italic</em> text');
    });

    it('handles multiple italic sections', () => {
      expect(formatInlineMarkdown('*first* and *second*')).toBe(
        '<em>first</em> and <em>second</em>',
      );
    });
  });

  describe('inline code formatting', () => {
    it('converts `code` to <code>code</code>', () => {
      expect(formatInlineMarkdown('Use the `console.log` function')).toBe(
        'Use the <code>console.log</code> function',
      );
    });

    it('handles multiple inline code sections', () => {
      expect(formatInlineMarkdown('`first` and `second`')).toBe(
        '<code>first</code> and <code>second</code>',
      );
    });

    it('escapes HTML inside code blocks', () => {
      expect(formatInlineMarkdown('Use `<div>` element')).toBe(
        'Use <code>&lt;div&gt;</code> element',
      );
    });
  });

  describe('combined formatting', () => {
    it('handles bold and italic together', () => {
      expect(formatInlineMarkdown('This is **bold** and *italic*')).toBe(
        'This is <strong>bold</strong> and <em>italic</em>',
      );
    });

    it('handles bold, italic, and code together', () => {
      expect(formatInlineMarkdown('**bold** *italic* `code`')).toBe(
        '<strong>bold</strong> <em>italic</em> <code>code</code>',
      );
    });

    it('handles ambiguous ***text*** (creates improperly nested but browser-renderable HTML)', () => {
      // Note: ***text*** is ambiguous and creates improperly nested HTML
      // Browsers still render this correctly, but proper nesting would require more complex parsing
      expect(formatInlineMarkdown('***text***')).toBe('<strong><em>text</strong></em>');
    });
  });

  describe('HTML escaping', () => {
    it('escapes HTML to prevent XSS', () => {
      expect(formatInlineMarkdown('<script>alert("xss")</script>')).toBe(
        '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;',
      );
    });

    it('escapes HTML while still applying markdown', () => {
      expect(formatInlineMarkdown('**<b>not nested</b>**')).toBe(
        '<strong>&lt;b&gt;not nested&lt;/b&gt;</strong>',
      );
    });

    it('escapes ampersands', () => {
      expect(formatInlineMarkdown('A & B')).toBe('A &amp; B');
    });
  });

  describe('edge cases', () => {
    it('returns plain text when no markdown', () => {
      expect(formatInlineMarkdown('Just plain text')).toBe('Just plain text');
    });

    it('handles empty string', () => {
      expect(formatInlineMarkdown('')).toBe('');
    });

    it('does not match unclosed markers', () => {
      expect(formatInlineMarkdown('This *is not closed')).toBe('This *is not closed');
    });
  });
});
