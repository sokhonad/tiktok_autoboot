/**
 * Root.tsx — Composition principale Remotion.
 * Définit la composition TechFRVideo utilisée pour le rendu headless.
 */

import React from "react";
import { Composition } from "remotion";
import { TechFRVideo, TechFRVideoProps } from "./TechFRVideo";

// Props par défaut pour le studio Remotion (preview)
const defaultProps: TechFRVideoProps = {
  topic: "5 f-strings Python que tu n'utilises pas encore",
  codeLines: [
    'name = "Alice"; age = 30',
    'print(f"{name!r} a {age} ans")',
    'pi = 3.14159',
    'print(f"Pi ≈ {pi:.2f}")',
    'x = 1000000',
    'print(f"{x:_}")',  // 1_000_000
  ],
  channelHandle: "@tech_fr",
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="TechFRVideo"
      component={TechFRVideo}
      durationInFrames={1800}  // 60s × 30fps
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
    />
  );
};
