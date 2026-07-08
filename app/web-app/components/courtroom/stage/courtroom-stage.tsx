"use client";

import { useEffect, useRef } from "react";
import {
  Application,
  Container,
  Graphics,
  Text,
  TextStyle,
} from "pixi.js";

import {
  getSceneLabel,
  getSpeakerShortName,
  isWitnessSpeaker,
  type TranscriptData,
} from "@/lib/courtroom";

type CourtroomStageProps = {
  activeSpeakerId: string;
  currentLineProgress: number;
  isPlaying: boolean;
  scene: string;
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
const WITNESS_OFFSTAGE_POSITION = { x: 1130, y: 490 };

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
  labelText: string,
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
    text: labelText,
    style: new TextStyle({
      fill: 0xf9f3e7,
      fontFamily: "IBM Plex Sans",
      fontSize: 17,
      fontWeight: "600",
    }),
  });
  label.anchor.set(0.5, 0);
  label.position.set(0, 138);
  container.addChild(label);

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

      const prosecutorTable = new Graphics();
      prosecutorTable.roundRect(88, 516, 256, 78, 18).fill(0x3f3027);
      world.addChild(prosecutorTable);

      const defenseTable = new Graphics();
      defenseTable.roundRect(938, 516, 256, 78, 18).fill(0x3f3027);
      world.addChild(defenseTable);

      const sceneRibbon = new Graphics();
      sceneRibbon.roundRect(464, 34, 352, 52, 26).fill({ color: 0x111827, alpha: 0.88 });
      world.addChild(sceneRibbon);

      const sceneText = new Text({
        text: "",
        style: new TextStyle({
          fill: 0xf7ebd6,
          fontFamily: "Cormorant Garamond",
          fontSize: 30,
          fontWeight: "700",
          letterSpacing: 2,
        }),
      });
      sceneText.anchor.set(0.5, 0.5);
      sceneText.position.set(640, 60);
      world.addChild(sceneText);

      const characterIds = Object.keys(props.transcript.voice_character_map);
      const characters = new Map<string, CharacterSprite>();

      characterIds.forEach((id) => {
        const isWitness = isWitnessSpeaker(id);
        const fixedPosition = FIXED_POSITIONS[id];
        const initialX = isWitness ? WITNESS_OFFSTAGE_POSITION.x : fixedPosition.x;
        const initialY = isWitness ? WITNESS_OFFSTAGE_POSITION.y : fixedPosition.y;
        const sprite = createCharacter(
          id,
          getSpeakerShortName(props.transcript, id),
          initialX,
          initialY,
        );
        world.addChild(sprite.container);
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
        sceneText.text = getSceneLabel(stateRef.current.scene).toUpperCase();

        characters.forEach((sprite, id) => {
          const isWitness = isWitnessSpeaker(id);
          const isActive = stateRef.current.isPlaying && stateRef.current.activeSpeakerId === id;
          const pulse = Math.sin(elapsedSeconds * (isActive ? 7.2 : 2.8));
          const speechProgress = stateRef.current.currentLineProgress;

          let targetX = sprite.baseX;
          let targetY = sprite.baseY;

          if (isWitness) {
            const isCurrentWitness = stateRef.current.witnessInBoxId === id;
            targetX = isCurrentWitness ? WITNESS_BOX_POSITION.x : WITNESS_OFFSTAGE_POSITION.x;
            targetY = isCurrentWitness ? WITNESS_BOX_POSITION.y : WITNESS_OFFSTAGE_POSITION.y;
          }

          sprite.container.x += (targetX - sprite.container.x) * 0.08;
          sprite.container.y += (targetY - sprite.container.y) * 0.08;
          sprite.container.y += Math.sin(elapsedSeconds * 1.9 + sprite.baseX / 100) * 0.15;
          sprite.arm.rotation = isActive ? 0.2 + pulse * 0.08 + speechProgress * 0.04 : 0.04 + pulse * 0.015;
          sprite.arm.alpha = isActive ? 1 : 0.86;
          sprite.speechGlow.alpha = isActive ? 0.6 + (pulse + 1) * 0.16 : 0.03;
          sprite.container.scale.set(isActive ? 1.02 : 0.985);
          sprite.body.tint = CHARACTER_COLORS[id] ?? 0xc9ba90;
          sprite.label.alpha = isActive ? 1 : 0.75;
        });
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
