# K3TEL Studio — 3D Atelier

A browser-based clothing concept design tool. All garment forms are original procedural meshes; no third-party brand logos, garment models or artwork are included. The optional K3TEL emblem is supplied by the brand owner.

## Design tools
- 13 garment forms: tee, hoodie, jersey, bomber jacket, cropped tee, tank top, jeans, cargos, shorts, skirt, dress, platform boots and knit top.
- Shape controls for width, length and sleeve/flare/depth.
- Body, secondary and trim colors; six fabric finishes and six all-over pattern choices.
- Four design surfaces with independent text/image layers. PNG, JPG and WebP uploads; optional removal of light backgrounds connected to image edges.
- Layer placement by dragging on the square design surface, or by position, scale, rotation and opacity controls. Reorder, duplicate, hide or remove layers.
- Orbit/zoom, fixed camera views and auto-rotation.
- Undo/redo (30 snapshots), automatic device-local saving, editable JSON project import/export.
- PNG studio image, 1024px surface PNG, and textured GLB model export.
- Desktop three-panel layout and phone panel tabs.

## Run locally
Use a current desktop or mobile browser with WebGL 2 enabled. Node.js is needed only to serve local files:

    node serve.mjs

Open the printed local URL. Keep the server running while designing. Do not open index.html directly as a file URL: ES modules require HTTP.

The downloadable folder bundles Three.js 0.170.0 and its MIT license, so the local app does not depend on a CDN. The GitHub Pages publication loads the same pinned library and addons from jsDelivr and reuses the portfolio's K3TEL emblem.

## Storage and artwork
Design data, image uploads and autosaves stay in the browser on that device; there is no account or cloud sync. A design saved on localhost does not automatically appear on the hosted site or another device. Download JSON projects as backups. Browser storage can be cleared or exceed its quota; the UI reports when a downloadable backup is needed. Up to 30 layers; image uploads up to 12MB are normalized to at most 1200px. Imported JSON files are validated and limited to 10MB.

## Scope
This is a visual concept designer with adjustable templates. It does not provide arbitrary mesh sculpting, custom topology import, physically accurate draping, body measurements, garment grading, stitch simulation, fabric consumption, sewing patterns or manufacturing-ready tech packs. Proportions are visual controls, not physical measurements. Artwork wraps according to each template's UV surfaces and can stretch near seams or curve edges. Front/back map to main panels, legs or toes; left/right map to sleeves, dress skirt panels or boot shafts. Artwork on an unused surface remains in the project.

## Verification
Geometry checked for all 13 garments at minimum, default and maximum proportions (39 combinations), with finite positions/normals/UVs and valid indices. Browser checks covered garment changes, proportion controls, text/image layers, logo background removal, undo/redo, autosave/reload, project reopen, camera controls and mobile panel switching. All four downloaded export formats were inspected; the GLB includes embedded textures and valid glTF 2 headers.

## Files
- index.html, studio.css: interface and responsive layout.
- studio.js: editor state, WebGL scene, controls and exports.
- garments.js: procedural garment geometry.
- painter.js: surface textures and artwork compositing.
- state.js: project schema and import validation.
- vendor/: Three.js and official OrbitControls/GLTFExporter addons.
