"use client";

import { useEffect, useRef } from "react";
import { Application, Container, Graphics, Text, TextStyle } from "pixi.js";

import {
  getSpeakerShortName,
  getWitnessSpeakerIds,
  isWitnessSpeaker,
  type TranscriptData,
} from "@/lib/courtroom";

type CourtroomStageProps = {
  activeSpeakerId: string | null;
  currentLineProgress: number;
  isPlaying: boolean;
  scene: string | null;
  transcript: TranscriptData;
  witnessInBoxId: string | null;
};

type CharacterSprite = {
  container: Container;
  body: Graphics;
  arm: Graphics;
  speechGlow: Graphics;
  label: Text;
  baseX: number;
  baseY: number;
};

const STAGE_WIDTH = 1280;
const STAGE_HEIGHT = 760;

const FIXED_POSITIONS: Record<string, { x: number; y: number }> = {
  judge: { x: 640, y: 152 },
  prosecution: { x: 230, y: 495 },
  defense: { x: 1040, y: 495 },
};

const WITNESS_BOX_POSITION = { x: 650, y: 410 };
const WITNESS_BENCH_LAYOUT = {
  centerX: 635,
  lowerRowY: 638,
  upperRowY: 624,
  maxWidth: 264,
  rowSpacing: 86,
};
const SEATED_WITNESS_SCALE = 0.66;
const ACTIVE_WITNESS_SCALE = 0.92;
const FIXED_CHARACTER_SCALE = 0.985;

const CHARACTER_COLORS: Record<string, number> = {
  judge: 0xd2b179,
  prosecution: 0x7c9fd8,
  defense: 0xd88963,
  W1: 0x94d1c3,
  W2: 0xa3b5e2,
  W3: 0xdca8c6,
  W5: 0xd4be8c,
};

function drawRoundedRect(
  graphics: Graphics,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
  color: number,
  alpha = 1,
) {
  graphics.clear();
  graphics.roundRect(x, y, width, height, radius).fill({ color, alpha });
}

function drawCircle(
  graphics: Graphics,
  x: number,
  y: number,
  radius: number,
  color: number,
  alpha = 1,
) {
  graphics.clear();
  graphics.circle(x, y, radius).fill({ color, alpha });
}

function createCharacter(
  id: string,
  x: number,
  y: number,
): CharacterSprite {
  const container = new Container();
  container.position.set(x, y);

  const shadow = new Graphics();
  drawRoundedRect(shadow, -44, 114, 88, 16, 8, 0x000000, 0.3);
  container.addChild(shadow);

  const torso = new Graphics();
  drawRoundedRect(torso, -42, 6, 84, 112, 26, CHARACTER_COLORS[id] ?? 0xc9ba90);
  container.addChild(torso);

  const head = new Graphics();
  drawCircle(head, 0, -16, 29, 0xf1dcc1);
  container.addChild(head);

  const arm = new Graphics();
  drawRoundedRect(arm, -9, -7, 18, 70, 9, 0xf1dcc1, 0.92);
  arm.pivot.set(0, 6);
  arm.position.set(36, 34);
  container.addChild(arm);

  const lapel = new Graphics();
  drawRoundedRect(lapel, -18, 28, 36, 52, 14, 0x10182a, 0.25);
  container.addChild(lapel);

  const speechGlow = new Graphics();
  drawCircle(speechGlow, 0, -68, 14, 0xf4d39d, 0.96);
  speechGlow.alpha = 0;
  container.addChild(speechGlow);

  const label = new Text({
    text: "",
    style: new TextStyle({
      fill: 0xf9f3e7,
      fontFamily: "Avenir Next, Segoe UI, Helvetica Neue, Arial, sans-serif",
      fontSize: 16,
      fontWeight: "600",
      letterSpacing: 0.5,
      stroke: { color: 0x09101d, width: 4, join: "round" },
    }),
  });
  label.anchor.set(0.5, 0);
  label.position.set(x, y + 138);

  return {
    container,
    body: torso,
    arm,
    speechGlow,
    label,
    baseX: x,
    baseY: y,
  };
}

function buildWitnessBenchPositions(witnessIds: string[]) {
  const positions = new Map<string, { x: number; y: number }>();

  if (witnessIds.length === 0) {
    return positions;
  }

  const rowCount = witnessIds.length > 4 ? 2 : 1;
  const firstRowCount = rowCount === 1 ? witnessIds.length : Math.ceil(witnessIds.length / 2);
  const rows = [witnessIds.slice(0, firstRowCount), witnessIds.slice(firstRowCount)];

  rows.forEach((rowWitnessIds, rowIndex) => {
    if (rowWitnessIds.length === 0) {
      return;
    }

    const y = rowIndex === 0 ? WITNESS_BENCH_LAYOUT.lowerRowY : WITNESS_BENCH_LAYOUT.upperRowY;
    const spread = Math.min(
      WITNESS_BENCH_LAYOUT.maxWidth,
      Math.max(0, (rowWitnessIds.length - 1) * WITNESS_BENCH_LAYOUT.rowSpacing),
    );
    const startX = WITNESS_BENCH_LAYOUT.centerX - spread / 2;

    rowWitnessIds.forEach((id, index) => {
      positions.set(id, {
        x: startX + index * WITNESS_BENCH_LAYOUT.rowSpacing,
        y,
      });
    });
  });

  return positions;
}

export function CourtroomStage(props: CourtroomStageProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const appRef = useRef<Application | null>(null);
  const stateRef = useRef(props);

  useEffect(() => {
    stateRef.current = props;
  }, [props]);

  useEffect(() => {
    let disposed = false;
    let resizeObserver: ResizeObserver | null = null;
    const host = hostRef.current;

    if (!host) {
      return;
    }

    const setup = async () => {
      const app = new Application();
      await app.init({
        antialias: true,
        backgroundAlpha: 0,
        resolution: Math.min(window.devicePixelRatio || 1, 2),
        resizeTo: host,
      });

      if (disposed) {
        await app.destroy();
        return;
      }

      appRef.current = app;
      app.canvas.style.display = "block";
      app.canvas.style.width = "100%";
      app.canvas.style.height = "100%";
      host.appendChild(app.canvas);
      app.renderer.resize(host.clientWidth, host.clientHeight);

      const world = new Container();
      app.stage.addChild(world);

      const backdrop = new Graphics();
      backdrop.rect(0, 0, STAGE_WIDTH, STAGE_HEIGHT).fill(0x0c1224);
      world.addChild(backdrop);

      const halo = new Graphics();
      halo.ellipse(STAGE_WIDTH / 2, 110, 420, 150).fill({ color: 0xf0cb8a, alpha: 0.09 });
      world.addChild(halo);

      const columns = new Graphics();
      columns
        .rect(120, 140, 44, 400)
        .rect(1116, 140, 44, 400)
        .rect(320, 92, 640, 26)
        .fill({ color: 0x1b2944, alpha: 0.72 });
      world.addChild(columns);

      const bench = new Graphics();
      bench
        .roundRect(400, 176, 480, 78, 22)
        .roundRect(454, 248, 372, 32, 16)
        .fill(0x37291f);
      world.addChild(bench);

      const floor = new Graphics();
      floor.rect(0, 570, STAGE_WIDTH, 190).fill(0x261d1a);
      for (let lane = 80; lane < STAGE_WIDTH; lane += 112) {
        floor.moveTo(lane, 570);
        floor.lineTo(lane + 70, 760);
      }
      floor.stroke({ width: 2, color: 0x4c3729, alpha: 0.5 });
      world.addChild(floor);

      const witnessBox = new Graphics();
      witnessBox
        .roundRect(560, 396, 166, 118, 18)
        .fill(0x49342a)
        .roundRect(560, 396, 166, 118, 18)
        .stroke({ width: 3, color: 0xd7b57f, alpha: 0.45 });
      world.addChild(witnessBox);

      const witnessBench = new Graphics();
      witnessBench
        .roundRect(455, 628, 360, 28, 14)
        .roundRect(483, 650, 304, 22, 10)
        .fill(0x433127);
      witnessBench
        .moveTo(511, 654)
        .lineTo(495, 718)
        .moveTo(759, 654)
        .lineTo(775, 718)
        .stroke({ width: 5, color: 0x2f221b, alpha: 0.9 });
      world.addChild(witnessBench);

      const witnessBenchLabel = new Text({
        text: "Witness",
        style: new TextStyle({
          fill: 0xf9f3e7,
          fontFamily: "Avenir Next, Segoe UI, Helvetica Neue, Arial, sans-serif",
          fontSize: 16,
          fontWeight: "600",
          letterSpacing: 0.5,
          stroke: { color: 0x09101d, width: 4, join: "round" },
        }),
      });
      witnessBenchLabel.anchor.set(0.5, 0);
      witnessBenchLabel.position.set(635, 723);
      world.addChild(witnessBenchLabel);

      const prosecutorTable = new Graphics();
      prosecutorTable.roundRect(88, 516, 256, 78, 18).fill(0x3f3027);
      world.addChild(prosecutorTable);

      const defenseTable = new Graphics();
      defenseTable.roundRect(938, 516, 256, 78, 18).fill(0x3f3027);
      world.addChild(defenseTable);

      const characterIds = Object.keys(props.transcript.voice_character_map);
      const witnessIds = getWitnessSpeakerIds(props.transcript);
      const witnessBenchPositions = buildWitnessBenchPositions(witnessIds);
      const characters = new Map<string, CharacterSprite>();

      characterIds.forEach((id) => {
        const isWitness = isWitnessSpeaker(id);
        const fixedPosition = FIXED_POSITIONS[id];
        const benchPosition = witnessBenchPositions.get(id);
        const initialX = isWitness ? benchPosition!.x : fixedPosition.x;
        const initialY = isWitness ? benchPosition!.y : fixedPosition.y;
        const sprite = createCharacter(id, initialX, initialY);
        if (isWitness) {
          sprite.container.scale.set(SEATED_WITNESS_SCALE);
        }
        world.addChild(sprite.container);
        world.addChild(sprite.label);
        characters.set(id, sprite);
      });

      const ticker = () => {
        const width = host.clientWidth;
        const height = host.clientHeight;
        const stageScale = Math.min(width / STAGE_WIDTH, height / STAGE_HEIGHT);

        world.scale.set(stageScale);
        world.position.set(
          (width - STAGE_WIDTH * stageScale) / 2,
          (height - STAGE_HEIGHT * stageScale) / 2,
        );

        const elapsedSeconds = performance.now() / 1000;

        characters.forEach((sprite, id) => {
          const isWitness = isWitnessSpeaker(id);
          const isActive = stateRef.current.isPlaying && stateRef.current.activeSpeakerId === id;
          const pulse = Math.sin(elapsedSeconds * (isActive ? 7.2 : 2.8));
          const speechProgress = stateRef.current.currentLineProgress;

          let targetX = sprite.baseX;
          let targetY = sprite.baseY;
          let targetScale = isWitness ? SEATED_WITNESS_SCALE : FIXED_CHARACTER_SCALE;
          let stride = 0;
          let armRotationBase = 0.04;

          if (isWitness) {
            const isCurrentWitness = stateRef.current.witnessInBoxId === id;
            const benchPosition = witnessBenchPositions.get(id)!;
            targetX = isCurrentWitness ? WITNESS_BOX_POSITION.x : benchPosition.x;
            targetY = isCurrentWitness ? WITNESS_BOX_POSITION.y : benchPosition.y;
            const distance = Math.hypot(targetX - sprite.container.x, targetY - sprite.container.y);
            const isWalking = distance > 26;

            targetScale = isCurrentWitness || isWalking ? ACTIVE_WITNESS_SCALE : SEATED_WITNESS_SCALE;
            stride = isWalking ? Math.sin(elapsedSeconds * 8.4 + sprite.baseX / 90) * 2.4 : 0;
            armRotationBase = isWalking ? 0.18 : 0.02;
          }

          sprite.container.x += (targetX - sprite.container.x) * 0.08;
          sprite.container.y += (targetY - sprite.container.y) * 0.08;
          sprite.container.y += stride + Math.sin(elapsedSeconds * 1.9 + sprite.baseX / 100) * 0.15;
          sprite.arm.rotation = isActive
            ? 0.2 + pulse * 0.08 + speechProgress * 0.04
            : armRotationBase + pulse * 0.015;
          sprite.arm.alpha = isActive ? 1 : 0.86;
          sprite.speechGlow.alpha = isActive ? 0.6 + (pulse + 1) * 0.16 : 0.03;
          const activeScaleBoost = isActive ? 0.04 : 0;
          const currentScale = sprite.container.scale.x;
          const nextScale = currentScale + (targetScale + activeScaleBoost - currentScale) * 0.12;
          sprite.container.scale.set(nextScale);
          sprite.body.tint = CHARACTER_COLORS[id] ?? 0xc9ba90;
          if (isWitness) {
            const isCurrentWitness = stateRef.current.witnessInBoxId === id;
            sprite.label.text = isCurrentWitness
              ? getSpeakerShortName(stateRef.current.transcript, id)
              : "";
            sprite.label.alpha = isCurrentWitness ? 1 : 0;
          } else {
            sprite.label.text = getSpeakerShortName(stateRef.current.transcript, id);
            sprite.label.alpha = 1;
          }
          sprite.label.position.set(targetX, targetY + 138 * targetScale);
        });

        const hasSeatedWitness = witnessIds.some((id) => stateRef.current.witnessInBoxId !== id);
        witnessBenchLabel.alpha = hasSeatedWitness ? 0.82 : 0;
      };

      app.ticker.add(ticker);

      resizeObserver = new ResizeObserver(() => {
        app.renderer.resize(host.clientWidth, host.clientHeight);
      });
      resizeObserver.observe(host);

      return () => {
        app.ticker.remove(ticker);
      };
    };

    let disposeTicker: (() => void) | undefined;

    void setup().then((cleanup) => {
      disposeTicker = cleanup;
    });

    return () => {
      disposed = true;
      disposeTicker?.();
      resizeObserver?.disconnect();
      const app = appRef.current;
      appRef.current = null;
      if (app) {
        void app.destroy(true, { children: true });
      }
      if (host.firstChild) {
        host.textContent = "";
      }
    };
  }, [props.transcript]);

  return (
    <div
      aria-label="Courtroom stage"
      className="flex h-full min-h-0 w-full items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,rgba(212,168,103,0.12),transparent_34%),linear-gradient(180deg,rgba(9,14,28,0.88),rgba(3,7,17,0.98))] p-0"
    >
      <div className="h-full w-full" ref={hostRef} />
    </div>
  );
}
