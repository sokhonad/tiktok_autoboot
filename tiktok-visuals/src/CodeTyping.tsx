/**
 * CodeTyping.tsx — Animation d'un bloc de code qui se tape progressivement.
 * Utilise Remotion interpolate pour un effet typewriter fluide.
 */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface CodeTypingProps {
  /** Lignes de code à animer */
  lines: string[];
  /** Frame de départ de l'animation */
  startFrame?: number;
  /** Couleur de fond du bloc code */
  bgColor?: string;
  /** Couleur du texte */
  textColor?: string;
  /** Vitesse : caractères par frame */
  charsPerFrame?: number;
}

// Couleurs syntaxiques minimalistes
const SYNTAX_COLORS: Record<string, string> = {
  keyword: "#c792ea",   // violet — def, class, for, if, return
  string: "#c3e88d",    // vert clair — "..." '...' f"..."
  number: "#f78c6c",    // orange — 0-9
  comment: "#546e7a",   // gris — #...
  function: "#82aaff",  // bleu — print(), len()
  default: "#eeffff",   // blanc cassé — reste
};

/** Coloration syntaxique simplifiée Python */
function highlightLine(line: string): React.ReactNode[] {
  // Regex basique pour les tokens Python courants
  const tokenRegex =
    /(#.*)|(f?"[^"]*"|f?'[^']*')|("""[\s\S]*?""")|(def |class |import |from |return |if |else:|elif |for |in |with |as |True|False|None|lambda )|(print|len|range|int|str|list|dict|type|input)(\()|([\d]+)/g;

  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(line)) !== null) {
    // Texte avant le match (non coloré)
    if (match.index > lastIndex) {
      nodes.push(
        <span key={`d-${lastIndex}`} style={{ color: SYNTAX_COLORS.default }}>
          {line.slice(lastIndex, match.index)}
        </span>
      );
    }

    // Détermine la couleur du token
    let color = SYNTAX_COLORS.default;
    if (match[1]) color = SYNTAX_COLORS.comment;
    else if (match[2] || match[3]) color = SYNTAX_COLORS.string;
    else if (match[4]) color = SYNTAX_COLORS.keyword;
    else if (match[5]) color = SYNTAX_COLORS.function;
    else if (match[7]) color = SYNTAX_COLORS.number;

    nodes.push(
      <span key={`t-${match.index}`} style={{ color }}>
        {match[0]}
      </span>
    );
    lastIndex = match.index + match[0].length;
  }

  // Reste de la ligne
  if (lastIndex < line.length) {
    nodes.push(
      <span key={`end-${lastIndex}`} style={{ color: SYNTAX_COLORS.default }}>
        {line.slice(lastIndex)}
      </span>
    );
  }

  return nodes.length > 0 ? nodes : [<span key="empty" style={{ color: SYNTAX_COLORS.default }}>{line}</span>];
}

export const CodeTyping: React.FC<CodeTypingProps> = ({
  lines,
  startFrame = 0,
  bgColor = "#1e1e2e",
  textColor = "#eeffff",
  charsPerFrame = 3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Nombre total de caractères déjà "tapés"
  const totalCharsTyped = Math.max(0, (frame - startFrame) * charsPerFrame);

  // Curseur clignotant : change toutes les 15 frames
  const showCursor = Math.floor(frame / 15) % 2 === 0;

  // Calcule quels caractères sont visibles ligne par ligne
  let charsRemaining = totalCharsTyped;
  const visibleLines = lines.map((line) => {
    if (charsRemaining <= 0) return "";
    const visible = line.slice(0, charsRemaining);
    charsRemaining = Math.max(0, charsRemaining - line.length);
    return visible;
  });

  // Opacité globale : fade-in sur les 10 premières frames
  const opacity = interpolate(frame - startFrame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity,
      }}
    >
      <div
        style={{
          backgroundColor: bgColor,
          borderRadius: 16,
          padding: "32px 40px",
          width: "90%",
          maxWidth: 960,
          boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
          border: "1px solid #2a2a3e",
          fontFamily: "'Fira Code', 'Courier New', monospace",
          fontSize: 28,
          lineHeight: 1.7,
        }}
      >
        {/* Barre de titre style VS Code */}
        <div
          style={{
            display: "flex",
            gap: 8,
            marginBottom: 20,
            alignItems: "center",
          }}
        >
          <div style={{ width: 14, height: 14, borderRadius: "50%", backgroundColor: "#ff5f57" }} />
          <div style={{ width: 14, height: 14, borderRadius: "50%", backgroundColor: "#febc2e" }} />
          <div style={{ width: 14, height: 14, borderRadius: "50%", backgroundColor: "#28c840" }} />
          <span style={{ color: "#546e7a", fontSize: 18, marginLeft: 8 }}>main.py</span>
        </div>

        {/* Lignes de code */}
        {visibleLines.map((lineText, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", minHeight: "1.7em" }}>
            {/* Numéro de ligne */}
            <span
              style={{
                color: "#3a3a4e",
                width: 36,
                textAlign: "right",
                marginRight: 20,
                userSelect: "none",
                flexShrink: 0,
                fontSize: 22,
              }}
            >
              {i + 1}
            </span>
            {/* Code coloré */}
            <span>{lineText && highlightLine(lineText)}</span>
            {/* Curseur sur la dernière ligne active */}
            {i === visibleLines.findLastIndex((l) => l.length > 0) &&
              charsRemaining <= 0 &&
              showCursor && (
                <span
                  style={{
                    display: "inline-block",
                    width: 3,
                    height: "1em",
                    backgroundColor: "#6c63ff",
                    marginLeft: 2,
                    verticalAlign: "middle",
                  }}
                />
              )}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
