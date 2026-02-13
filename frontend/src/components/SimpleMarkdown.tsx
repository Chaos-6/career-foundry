/**
 * Lightweight markdown renderer for evaluation output.
 *
 * Handles the most common markdown patterns Claude generates:
 * - Headers (##, ###, ####)
 * - Bold (**text**)
 * - Italic (*text*)
 * - Bullet lists (- item)
 * - Numbered lists (1. item)
 * - Horizontal rules (---)
 * - Code blocks (```code```)
 *
 * Not a full markdown parser — just enough for evaluation display.
 */

import React from "react";
import { Box, Divider, Typography } from "@mui/material";

interface SimpleMarkdownProps {
  content: string;
}

export default function SimpleMarkdown({ content }: SimpleMarkdownProps) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];

  lines.forEach((line, i) => {
    // Code blocks
    if (line.trim().startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <Box
            key={`code-${i}`}
            component="pre"
            sx={{
              bgcolor: "grey.100",
              p: 2,
              borderRadius: 1,
              overflowX: "auto",
              fontSize: "0.85rem",
              fontFamily: "monospace",
              my: 1,
            }}
          >
            {codeBuffer.join("\n")}
          </Box>
        );
        codeBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      return;
    }

    const trimmed = line.trim();

    // Empty lines
    if (!trimmed) {
      return;
    }

    // Horizontal rules
    if (/^[-━═]{3,}$/.test(trimmed)) {
      elements.push(<Divider key={`hr-${i}`} sx={{ my: 2 }} />);
      return;
    }

    // Headers
    if (trimmed.startsWith("#### ")) {
      elements.push(
        <Typography key={`h4-${i}`} variant="subtitle1" fontWeight={600} sx={{ mt: 2, mb: 0.5 }}>
          {formatInline(trimmed.slice(5))}
        </Typography>
      );
      return;
    }
    if (trimmed.startsWith("### ")) {
      elements.push(
        <Typography key={`h3-${i}`} variant="h6" sx={{ mt: 2.5, mb: 1 }}>
          {formatInline(trimmed.slice(4))}
        </Typography>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(
        <Typography key={`h2-${i}`} variant="h5" sx={{ mt: 3, mb: 1 }}>
          {formatInline(trimmed.slice(3))}
        </Typography>
      );
      return;
    }

    // Bullet lists
    if (/^[-*]\s/.test(trimmed)) {
      elements.push(
        <Typography
          key={`li-${i}`}
          variant="body2"
          component="div"
          sx={{ pl: 2, mb: 0.5, display: "flex", gap: 1 }}
        >
          <span>•</span>
          <span>{formatInline(trimmed.slice(2))}</span>
        </Typography>
      );
      return;
    }

    // Numbered lists
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      elements.push(
        <Typography
          key={`ol-${i}`}
          variant="body2"
          component="div"
          sx={{ pl: 2, mb: 0.5, display: "flex", gap: 1 }}
        >
          <span style={{ fontWeight: 600, minWidth: 20 }}>{numMatch[1]}.</span>
          <span>{formatInline(numMatch[2])}</span>
        </Typography>
      );
      return;
    }

    // Checkbox items
    if (trimmed.startsWith("- [x]") || trimmed.startsWith("- [ ]")) {
      const checked = trimmed.startsWith("- [x]");
      const text = trimmed.slice(6);
      elements.push(
        <Typography
          key={`check-${i}`}
          variant="body2"
          component="div"
          sx={{
            pl: 2,
            mb: 0.5,
            fontWeight: checked ? 600 : 400,
            color: checked ? "secondary.main" : "text.primary",
          }}
        >
          {checked ? "✓" : "○"} {formatInline(text)}
        </Typography>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <Typography key={`p-${i}`} variant="body2" sx={{ mb: 1 }}>
        {formatInline(trimmed)}
      </Typography>
    );
  });

  return <Box>{elements}</Box>;
}

/**
 * Format inline markdown: bold, italic, inline code.
 */
function formatInline(text: string): React.ReactNode {
  // Split on bold, italic, and inline code patterns
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold: **text**
    const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
    // Italic: *text*
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/);
    // Inline code: `text`
    const codeMatch = remaining.match(/`(.*?)`/);

    // Find the earliest match
    const matches = [
      boldMatch ? { match: boldMatch, type: "bold" as const } : null,
      italicMatch ? { match: italicMatch, type: "italic" as const } : null,
      codeMatch ? { match: codeMatch, type: "code" as const } : null,
    ]
      .filter(Boolean)
      .sort((a, b) => a!.match.index! - b!.match.index!);

    if (matches.length === 0) {
      parts.push(remaining);
      break;
    }

    const first = matches[0]!;
    const idx = first.match.index!;

    // Text before the match
    if (idx > 0) {
      parts.push(remaining.slice(0, idx));
    }

    // The formatted content
    const content = first.match[1];
    switch (first.type) {
      case "bold":
        parts.push(
          <strong key={key++}>{content}</strong>
        );
        break;
      case "italic":
        parts.push(
          <em key={key++}>{content}</em>
        );
        break;
      case "code":
        parts.push(
          <code
            key={key++}
            style={{
              backgroundColor: "#edf2f7",
              padding: "1px 4px",
              borderRadius: 3,
              fontSize: "0.9em",
            }}
          >
            {content}
          </code>
        );
        break;
    }

    remaining = remaining.slice(idx + first.match[0].length);
  }

  return <>{parts}</>;
}
