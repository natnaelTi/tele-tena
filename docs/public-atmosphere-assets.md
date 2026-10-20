# Public Atmosphere Asset Provenance

Generated with the built-in image-generation tool for this project, then optimized
as WebP. No external photograph, real practitioner, patient record or actual
TeleTena facility is represented. Source PNGs remain outside Git in the local
Codex generated-images directory. Hover/focus captions disclose the conceptual images; the earlier v1 checkpoint used inline captions.
No image-generation or other API secret is embedded in frontend assets.

## Room

Project path: `frontend/public/public-experience/consultation-room-v1.webp`.
SHA256: `5b10aaba45c29c5ddcc3be210b0b815a19e5a552d4ba6b55bf30a07dd6373ca3`.

Final built-in prompt:

> Use case: photorealistic-natural. Project asset for TeleTena public hero, landscape 3:2. An inviting premium private adult counseling consultation room, no people. Cozy Ethiopian contemporary bohemian design, elegant curved cream armchairs facing each other, warm wood, subtle woven Ethiopian textile accents, indoor plants, sculptural warm lamps, discreet coffee corner with traditional Ethiopian jebena, small incense vessel with a faint delicate rising smoke wisp. Natural tactile materials, clean professional calm environment, cinematic editorial interior photography. Deep blue teal #145D7A and #087F8C shadows blend at left edge into dark blue, warm natural light on right. Wide well composed view, furniture fully visible, no text, no logos, no watermark, no clinical equipment, no claims this is a real facility.

## Connected Practice

Project path: `frontend/public/public-experience/connected-practice-v1.webp`.
SHA256: `1ef1145007c6617a56503159f8a9750c8c08c274e2e8d90e8446abbce98d001b`.

Final built-in prompt:

> Use case: stylized-concept photorealistic. Asset: TeleTena website hero landscape 3:2. A faceless anonymous Ethiopian adult clinician viewed from behind and three-quarter back, seated in a beautiful consultation armchair, holding and looking at a smartphone. Cozy premium professional office, warm wood, subtle Ethiopian woven textile accents, leafy plants, soft sculptural lighting, deep teal blue shadows at left blending with #145D7A, warm light at right. Above phone floats a restrained elegant translucent holographic arrangement of three video consultation screen frames showing anonymous faceless adult patient silhouettes and a clinician silhouette. Conceptual future-facing illustration, no legible text, no logos, no identifiable people, no screens of actual records, no white medical coat required. Cinematic carefully composed realistic interior materials, serene welcoming mood, no sci-fi clutter. Screens are conceptual, do not imply actual hologram feature.

The dimensional stethoscope, gradients, smoke, waves, light and interface interactions
are repository-native SVG/CSS/React, not generated executable code or heavy3D assets.

## Annotated Hero Correction, v2

The owner's annotated screenshot was visually inspected outside Git. It is not
an application asset and is not copied here. Existing v1 files remain unchanged.
The built-in image tool edited the v1 images; transparent RGBA outputs were
converted to WebP without changing composition. No external image service or
background-removal package was used. Source/discarded PNGs remain outside Git.

### Patient Room Stage

Project path: `frontend/public/public-experience/consultation-room-stage-v2.webp`.
SHA256: `d7e8e2ef5ce21fb5be7c2f9449cd36318593667141f6c7edf40200f8fa1e522f`.
1536×1024 RGBA;430361 fully transparent pixels. The solid wall is actually removed,
not merely painted blue. The removed plant is the blurry foreground plant; the
background tree/decor remains. The image is rendered uncropped with no oval mask.

Selected built-in edit prompt (reference1 original room, reference2 owner annotation):

> Edit target: image1 original room. Image2 is ONLY the owner's annotated composition reference, do not include markings, text, browser, hero copy or blue background in output. Create a photorealistic transparent-background architectural room diorama CUTOUT based closely on image1. Keep the two cream armchairs, Ethiopian woven cushions, central wood coffee table, left wood coffee cabinet with jebena, lamp and incense, woven wall basket and hanging textile, shelving plants and warm lights, right window with distant city view and right floor lamp. REMOVE the large blurry foreground plant at lower left. REMOVE the entire solid blue left/back WALL, making those areas genuinely transparent so the website blue background will become the wall; keep the hanging basket and textile as independent suspended decor with soft lighting/contact shadows in alpha where feasible. Preserve beautiful natural light and shadows on furniture and stage. Compose the rug as a bounded perspective quadrilateral fully within a slightly larger raised wood platform, platform about 8cm thick with clearly visible front and right edges, like a floating 3D stage. ALL rug corners, platform corners and furniture boundaries must be fully visible and UNCUT, not fading away, surrounded by a modest transparent margin. Expand the view slightly to fit the entire floor stage and room setup in one landscape frame, furniture kept large. No exterior floor outside platform, no extra wall or ceiling, no background fill, no opaque rectangle or artificial gradient, no caption, no words, no logos, no annotation. Keep the elegant Ethiopian consultation room's design and camera perspective. Real transparent alpha output.

### Clinician Gown / Stethoscope

Project path: `frontend/public/public-experience/connected-practice-v2.webp`.
SHA256: `60af50080c3cb845d4630a23a2f6da7fd46b3910907958b170fbbb527653c28e`.
1536×1024 RGBA;175776 fully transparent pixels. Original scene arrangement/crop
is retained, with a white gown and teal stethoscope on the viewer-right armrest.
Generated details have small variations; this is not pixel-identical source
preservation. CSS feathers only narrow boundaries to blend the existing crop.

Selected built-in edit prompt (original v1 practice image):

> Minimal precise edit of this ORIGINAL photograph. Preserve the exact framing, crop, scale, camera viewpoint, clinician pose/hair/clothes/phone, every hologram screen and participant, original cabinet and lamp, original right window and plants, and original chair. Do NOT zoom out, do NOT add furniture or a new stage, do NOT replace the scene, do NOT move any existing object. ONLY add a neatly folded/draped white medical gown on the chair's visible right armrest (viewer right, across the visible near/right wooden arm area) with a teal stethoscope laid on the gown. Also extract the opaque plain teal wall at the left/behind the existing objects into transparent alpha, while leaving all objects and the bright right window/city view unchanged. Preserve soft light/shadow halos close to objects on alpha; no broad colored background fill. Existing furniture framing/crop must remain exactly as the original. No text/captions/annotations. Output genuine RGBA transparency where the wall was. Two changes only: wall removal and gown/stethoscope.
