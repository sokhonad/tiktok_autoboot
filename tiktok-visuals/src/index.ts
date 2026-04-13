/**
 * index.ts — Point d'entrée Remotion.
 * Exporte la composition root pour le CLI remotion render.
 */

import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
