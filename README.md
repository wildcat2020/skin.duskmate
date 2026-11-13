# Duskmate skin for Kodi

Duskmate is the Duskmate skin for Kodi 21. It is a derivative of
**Estuary**, Kodi's default skin, by phil65 and Ichabod Fletchman (Team Kodi).

- Code: GNU General Public License, version 2.0 (see `LICENSE.txt`).
- Artwork: Creative Commons Attribution-ShareAlike 4.0.
- Roboto fonts: Apache License 2.0 (`fonts/roboto_license.txt`).

Duskmate stays under the same licences as Estuary.

## What differs from Estuary (0.2.1)

- `colors/defaults.xml`: the Dusk palette (see `BRAND.md` at the repository root).
- `xml/Font.xml`: Roboto in the default font set.
- `media/buttons`, `media/dialogs`, `media/lists`: redrawn controls with rounded corners
  (buttons, dialog panels, list focus bar, poster focus frame) and a new toggle switch.
- Texture `border` values in the XML raised to suit the rounded corners.
- Text that used the focus colour now uses the lighter `focus_text`, which stays legible on dark.
- `xml/DialogSeekBar.xml`: a slimmer, amber progress line and a pause screen that dims the
  picture and shows title, details, plot and end time.
- `xml/Variables.xml`: the `DuskmatePause*` variables used by the pause screen.
- `media/duskmate/`: the Duskmate logo (home and login screens), the rounded tile focus
  texture and a flat fallback tile.
- `addon.xml`: identity and credits.

Everything else is Estuary as shipped with Kodi 21 (Omega).
