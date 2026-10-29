# Build and validation report

Status: candidate; physical PSP and emulator tests have not been performed. Artwork does not yet accurately reproduce every weapon. Visuals and previews are fan-made approximations.

- Build: `python3 tools/build.py` completed with Pillow 12.3.0.
- File: `dist/TMNT_PSP_Theme.ptf`, 482,652 bytes, below PTF Studio's 768 KiB preflight threshold.
- SHA-256: `36a55475fd037c4d5c63a9414eb129eacf1ba880138cdb55f1eacd71ce94dc58`.
- Structural and graphics check: `node tools/validate.cjs` read each group and inflated its records; PTF Studio's independent GIM decoder decoded 72 resources and checked their expected dimensions without errors. The 24-bit BMP wallpaper is 480 × 272. The theme contains 8 category, 58 first-level (29 body/focus pairs), and 4 second-level records.
- All 39 PNG icon exports have transparency. Native wallpaper dimensions are 480 × 272.
- Focus graphics are carried over from the PTF Studio sample. Previews use exported icons and wallpaper but approximate PSP positioning and labels; they do not simulate firmware rendering, selection glow, all model-specific menu content or pixel-perfect text.
- Missing validation: importing into an independent PTF editor, emulator or real PSP; model/firmware compatibility and user-facing behavior have not been verified.
- Known visual limitation: generated Raphael weapon details need refinement; Splinter, Shredder and Foot Clan are not represented. This build does not meet the full requested art direction or quality bar.
