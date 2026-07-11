# Web App Architecture

## Target Folder Breakdown

```text
app/
  page.tsx                  # route entry, composition only
components/
  courtroom/
    courtroom-page.tsx      # top-level client composition
    courtroom-header.tsx    # case header and summary
    caption-feed.tsx        # active subtitle surface
    docket-timeline.tsx     # turn queue
    playback-controls.tsx   # progress rail and transport
    courtroom-stage-panel.tsx
    stage/
      courtroom-stage.tsx   # PixiJS-only rendering
hooks/
  use-courtroom-manifest.ts # fallback + generated manifest loading
  use-courtroom-playback.ts # playback state and transport
lib/
  courtroom.ts              # transcript parsing and shared helpers
```

## Concern Mapping From `components/courtroom-app.tsx`

- Manifest bootstrap and source labeling move to `hooks/use-courtroom-manifest.ts`
- Playback transport, timeline fallback, and progress calculation move to `hooks/use-courtroom-playback.ts`
- Header content moves to `components/courtroom/courtroom-header.tsx`
- Caption surface moves to `components/courtroom/caption-feed.tsx`
- Progress rail and transport controls move to `components/courtroom/playback-controls.tsx`
- Turn queue moves to `components/courtroom/docket-timeline.tsx`
- Stage shell composition moves to `components/courtroom/courtroom-stage-panel.tsx`
- PixiJS canvas rendering remains isolated in `components/courtroom/stage/courtroom-stage.tsx`

## Styling Split

Keep global:
- design tokens in `app/globals.css`
- body background, selection, and shared panel utility classes
- font variables and reduced-motion rules

Move to component-level primitives:
- page and section layout classes
- panel internals for header, timeline, and controls
- stateful styling for active turns, playback mode pills, and transport buttons

## Refactor Goal

Route files stay thin, stage rendering stays isolated, and playback logic becomes reusable without coupling it to the full page shell.
