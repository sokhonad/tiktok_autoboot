/**
 * TechFRVideo.tsx — Composition vidéo principale.
 * Fond dark animé, titre, animation CodeTyping, CTA final.
 */

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CodeTyping } from "./CodeTyping";

export interface TechFRVideoProps {
  topic: string;
  codeLines: string[];
  channelHandle: string;
}

/** Arrière-plan animé avec dégradé et particules */
const AnimatedBackground: React.FC = () => {
  const frame = useCurrentFrame();

  // Légère oscillation de teinte pour l'animation
  const hueShift = interpolate(frame, [0, 900, 1800], [240, 260, 240]);

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(
          160deg,
          hsl(${hueShift}, 30%, 6%) 0%,
          hsl(${hueShift + 20}, 40%, 10%) 50%,
          hsl(${hueShift}, 25%, 7%) 100%
        )`,
      }}
    />
  );
};

/** Barre de progression en bas */
const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = frame / durationInFrames;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: 6,
          width: `${progress * 100}%`,
          background: "linear-gradient(90deg, #6c63ff, #a855f7)",
          borderRadius: "0 4px 4px 0",
        }}
      />
    </AbsoluteFill>
  );
};

/** Header avec handle et badge "tech" */
const Header: React.FC<{ handle: string }> = ({ handle }) => {
  const frame = useCurrentFrame();

  const translateY = interpolate(frame, [0, 20], [-60, 0], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          padding: "28px 40px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, transparent 100%)",
          transform: `translateY(${translateY}px)`,
          opacity,
        }}
      >
        <span
          style={{
            color: "white",
            fontSize: 36,
            fontWeight: 800,
            fontFamily: "system-ui, -apple-system, sans-serif",
            letterSpacing: -1,
          }}
        >
          {handle}
        </span>
        <div
          style={{
            background: "linear-gradient(135deg, #6c63ff, #a855f7)",
            borderRadius: 20,
            padding: "8px 20px",
            color: "white",
            fontSize: 24,
            fontWeight: 700,
            fontFamily: "system-ui, sans-serif",
          }}
        >
          TECH
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Titre de la vidéo avec animation spring */
const Title: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 1 },
    from: 0.8,
    to: 1,
  });

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        paddingTop: 140,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          textAlign: "center",
          padding: "0 40px",
        }}
      >
        <p
          style={{
            color: "white",
            fontSize: 44,
            fontWeight: 800,
            fontFamily: "system-ui, -apple-system, sans-serif",
            lineHeight: 1.3,
            textShadow: "0 2px 20px rgba(108, 99, 255, 0.5)",
            margin: 0,
          }}
        >
          {text}
        </p>
      </div>
    </AbsoluteFill>
  );
};

/** CTA animé en bas de vidéo (dernières 90 frames = 3s) */
const CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const ctaStartFrame = durationInFrames - 90;
  const localFrame = frame - ctaStartFrame;

  const opacity = interpolate(localFrame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const translateY = interpolate(localFrame, [0, 15], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (frame < ctaStartFrame) return null;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 40,
          right: 40,
          opacity,
          transform: `translateY(${translateY}px)`,
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, #6c63ff, #a855f7)",
            borderRadius: 20,
            padding: "20px 32px",
            textAlign: "center",
            boxShadow: "0 8px 32px rgba(108, 99, 255, 0.4)",
          }}
        >
          <p
            style={{
              color: "white",
              fontSize: 34,
              fontWeight: 800,
              margin: 0,
              fontFamily: "system-ui, sans-serif",
            }}
          >
            🔗 Lien en bio !
          </p>
          <p
            style={{
              color: "rgba(255,255,255,0.8)",
              fontSize: 26,
              margin: "8px 0 0 0",
              fontFamily: "system-ui, sans-serif",
            }}
          >
            Suis @tech_fr pour plus 🚀
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const TechFRVideo: React.FC<TechFRVideoProps> = ({
  topic,
  codeLines,
  channelHandle,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // L'animation de code commence à 45 frames (1.5s)
  const codeStartFrame = 45;

  // Fade-out du titre après 120 frames (4s)
  const titleOpacity = interpolate(frame, [90, 120], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <AnimatedBackground />
      <Header handle={channelHandle} />

      {/* Titre avec fade-out */}
      <div style={{ opacity: titleOpacity }}>
        <Title text={topic} />
      </div>

      {/* Animation code (s'affiche après le titre) */}
      {frame >= codeStartFrame && (
        <div
          style={{
            opacity: interpolate(frame, [codeStartFrame, codeStartFrame + 20], [0, 1], {
              extrapolateRight: "clamp",
            }),
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
          }}
        >
          <CodeTyping
            lines={codeLines}
            startFrame={codeStartFrame}
            charsPerFrame={2}
          />
        </div>
      )}

      <CTA />
      <ProgressBar />
    </AbsoluteFill>
  );
};
