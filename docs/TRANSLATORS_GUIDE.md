# Creating a Reconquered language pack with Claudius

This guide is for translators creating **their own language packs**, not only
Portuguese. Start with one mission and text; add narration and music once the
text works. You do not need to rebuild the engine for each translation.

Claudius is a community integration build based on Augustus, not an official
Augustus or Reconquered release. It remains experimental: **back up your files
and test separately before using important saves**.

## 1. Download a compatible build

Use [Claudius v0.1.0-alpha.2](https://github.com/csfreitas/augustus/releases/tag/claudius-v0.1.0-alpha.2),
based on engine commit `26e0508921bcb1c01166fc683a59fb1917fa2426`:

- **Windows x64:** download `Claudius-v0.1.0-alpha.2-windows-x64-SDL2.zip`.
  Extract the complete package into a new folder, keeping `assets/` beside the
  executable, which is still named `augustus.exe`.
- `Claudius-v0.1.0-alpha.2-assets.zip` is for developers using a matching build;
  it is **not** the executable. Do not mix alpha.1 assets with this build.
- Check `SHA256SUMS.txt` and the release README, including the Microsoft Visual
  C++ Redistributable x64 requirement. Do not obtain DLLs from unofficial sites.

You also need your own legitimate Caesar III data and Marek's public Reconquered
campaign. Neither is included. The PT-BR reference targets the public baseline
identified as `fileid=2243`; record the exact version you translate and recheck
your pack after campaign updates.

**Alpha.1 is too old for the complete workflow below.** Text localization alone
is not enough for localized audio, metadata and imperial names together. Other
platforms need a compatible build and separate testing; this ZIP is Windows x64.

The [reference CI run](https://github.com/csfreitas/augustus/actions/runs/35470768723)
also has development artifacts. These require a GitHub login and expire; see
[GitHub's instructions](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).
Prefer the release above for a stable download link.

## 2. Prepare a test campaign and choose your language

1. Close Augustus/Claudius. Back up the existing user directory, campaign and saves.
   Extract Claudius separately instead of replacing your working installation.
2. **A separate executable folder does not isolate the profile.** Claudius shares
   Augustus preferences, including `user_dir.txt` and `data_dir.txt`. A separate
   OS account or VM provides stronger isolation. Otherwise record the existing
   paths, use **Configuration / General Settings / User directory** to select a
   test directory, and restore the original setting afterwards. Never run both
   builds simultaneously against the same profile.
3. Put a private copy of the campaign in the test user directory's
   `campaigns/Reconquered Campaign/`. Keep its original folder name, `Settings.xml`,
   scenario filenames and source files. Author against an unpacked campaign first.
4. Select your language in the game configuration. Campaign overlays **do not add
   entries to the game's language menu**. The base-game language or a valid,
   legitimately obtained game-language directory must be available. Such a
   directory is recognized through its game text/message files, not through a
   campaign's `localization/` folder.

There is no `--userdirectory` option in this build. Its positional data-directory
argument selects Caesar III data, not an isolated profile. The log's
`Pref dir location:` entry identifies the preferences directory.

## 3. Create a locale folder

These examples use **`fr` as an example**, not a required language. Replace it
with the locale you actually support. Inside the existing campaign:

```text
Reconquered Campaign/
  Settings.xml                         original; unchanged
  scenario/                            original; unchanged
  localization/
    locales.xml                        optional, shared registry
    fr/
      campaign.xml
      messages/RC01 Ostia.xml
      media/RC01 Ostia.xml              optional speech/music references
      audio/RC01_intro_fr.wav           your own optional narration
      audio/RC01_briefing_fr.wav        your own optional music
      empire/RC01 Ostia.xml             optional imperial display names
```

`fr` works directly when the selected directory is `fr`, or the default game
language is detected as French and no other default mapping applies. For aliases
or an explicit default mapping, merge this entry into `localization/locales.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<locales version="1">
    <locale id="fr" aliases="fr-fr|fr_FR|french" default-for="fr"/>
</locales>
```

**Do not overwrite another pack's `locales.xml`.** Preserve its other entries;
resolve conflicting aliases/defaults with the other pack's author. If no registry
exists, create it using the complete example above. For a regional folder such
as `fr-FR`, change the ID, directory and examples consistently rather than keeping
competing entries.

An explicit language selection tries the directory, its supported normalization,
then matching aliases. With no directory selected, `default-for` uses the detected
base language; without a mapping, the neutral language code is tried. There is no
general regional fallback such as `fr-CA` automatically using `fr`. The `language`
attribute below is descriptive: actual paths and locale resolution select the pack.

## 4. Translate messages

Read the public original message XMLs for the existing UIDs and meaning. Create
`localization/fr/messages/RC01 Ostia.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<localization version="1" language="fr">
    <message uid="intro">
        <title>Première colonie romaine - test FR</title>
        <subtitle>Fondation d'Ostie</subtitle>
        <text>Bienvenue à Ostie. @L Ceci est un test de traduction.</text>
    </message>
</localization>
```

This is a **small authoring example**, not a complete French translation.
`intro` is a real RC01 UID. Add your own translations while keeping every UID
exactly as in the source, including case and spaces. Only `title`, `subtitle`
and `text` belong here. A canonical/editor export with a `<messages>` root is a
different format; do not copy it wholesale as an overlay or modify event triggers.

Omitted or empty fields keep the original text. Duplicate UIDs or malformed XML
can reject the whole overlay. An invalid file already found does not trigger a
retry in another locale folder. Translations are not merged field-by-field
between languages. Inspect the game log when fallback is unexpected.

Write UTF-8 with literal accented characters. The game converts text to its active
encoding: this does **not** add font glyphs or unrestricted Unicode support.
Check large titles and body text. Use explicit opening and closing root tags,
even for an empty overlay.

Preserve markup such as `@H`, `@L`, `@P` and `@G[image.png]`, including the original
image identifiers. Use `@0word` for highlights; a highlighted number needs a space,
such as `@0 32`, not `@032` (a link ID). Avoid accidentally turning translated
word prefixes into control codes.

The current game XML reader does not generally decode entities into display
characters. Do not encode accents as numeric entities. For text containing `&`
or `<`, use CDATA instead of relying on entity decoding:

```xml
<text><![CDATA[Texte de test : A & B. @L Deuxième ligne.]]></text>
```

## 5. Translate campaign and scenario metadata

Create `localization/fr/campaign.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<campaign_localization version="1" language="fr">
    <name>Reconquered - test FR</name>
    <description>Traduction française en cours de validation.</description>
    <mission first-scenario="RC01 Ostia">
        <title>Première colonie romaine</title>
    </mission>
    <scenario file="RC01 Ostia">
        <name>Ostie - test FR</name>
        <description>Établissez votre première colonie.</description>
    </scenario>
</campaign_localization>
```

Add entries for other missions/scenarios. `first-scenario` identifies the actual
first scenario of the mission, not its list position. `file` is the exact scenario
filename stem, without directory or extension. Read these keys from `Settings.xml`;
both `.mapx` and `.svx` are supported. Matching is case-sensitive.
Do not translate these keys or rename maps/the campaign directory. Author, rank,
progression and save identities are not translated by this schema.

## 6. Add narration and music

First make the matching text overlay work. Then create
`localization/fr/media/RC01 Ostia.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<media_localization version="1" language="fr">
    <message uid="intro">
        <speech filename="RC01_intro_fr.wav"/>
        <background_music filename="RC01_briefing_fr.wav"/>
    </message>
</media_localization>
```

Put those files in `localization/fr/audio/`. Use recordings/music you created or
have permission to distribute. Start with ordinary PCM WAV files and test playback
in the target build; changing an extension is not conversion. Keep voice and music
separate so their volume controls remain useful. Check clipping, music masking
speech, pronunciation and correspondence with the translated text.

Use short ASCII filenames with exact matching case. No subdirectories, drive
letters, leading/trailing dots or spaces, Windows reserved names, or
`< > : " / \ | ? *`. Each reference is a filename, not a path.

An event may provide only `<speech .../>`; omit `<background_music>` unless you
intend a specific track. Start with briefing/victory music and test events and
fanfares separately. This format covers **speech and background music**, not
translated images or videos.

Media follows the locale of the **valid message XML actually loaded for the same
scenario**. A media companion alone is insufficient. Keeping a textual entry for
each narrated UID is a useful authoring convention. Missing speech/music falls
back independently to the canonical media. Invalid media XML does not discard
valid translated text. A present but corrupt audio file is not guaranteed to fall
back: listen to the recordings, not just check their names.

## 7. Optional imperial city names

Create `localization/fr/empire/RC01 Ostia.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<empire_localization version="1">
    <city object-id="13" source="Ostia">
        <name>Ostie</name>
    </city>
</empire_localization>
```

This ID/name pair belongs to the supported RC01 baseline. For other cities/maps,
obtain the actual empire object ID and original name from scenario data or the
author. Do not guess from the city's position in a list. Keep `object-id` and
`source` unchanged; translate only `<name>`. A source mismatch keeps the original.
This changes runtime presentation, not trade logic, editor data or serialized
save names. Revalidate the guards when a campaign changes.

## 8. Match Reconquered's scenario filenames

The overlay filename follows the selected scenario in `Settings.xml`, **not** the
name of a source XML ending in `corrected.xml`. In the supported public baseline:

| Source overlay stem | Also required for the selected scenario |
|---|---|
| `RC08 Mediolanum` | `RC08 Mediolanum SAVE` |
| `RC10 Carthago` | `RC10 Carthago SAVE` |
| `RC11 Tarsus` | `RC11 Tarsus SAVE` |
| `RC13 Valentia` | `RC13 Valencia` |
| `RC14 Lutetia` | `RC14 Lutetia SAVE` |
| `RC17 Londinium` | `RC17 Londinium SAVE` |
| `RC19 Lindum` | `RC19 Lindum SAVE` |

Copy your corresponding message/media overlays to the required filenames and
keep them synchronized. Imperial overlays need the six `SAVE` aliases too; RC13's
imperial overlay already uses `Valencia`. Metadata keys also match the actual
scenario. The PT-BR alias generator is hardcoded to its locale: do not run it
unchanged to generate another language's files.

## 9. Build a translation-only ZIP

Create a **new, empty staging folder**, not an archive of your installed campaign:

```text
Reconquered-fr-0.1.0/
  README.md
  SHA256SUMS.txt
  locales-entry.xml.example
  payload/
    Reconquered Campaign/
      localization/
        fr/
          campaign.xml
          messages/...
          media/...
          empire/...
          audio/...
```

Include only implemented overlays and media you may distribute. The locale-entry
example is a merge instruction, **not** a replacement shared registry. Document
language, pack version, exact campaign baseline, required Claudius release,
covered missions, missing content, media credits, installation/removal and actual
test results. Generate SHA-256 checksums and a relative file list for safe removal.

Compress the staging folder with a ZIP tool. Large audio may be split into ZIPs
that extract into the same folder structure; list every required volume. Do not
include maps, saves, profiles, `Settings.xml`, canonical message XMLs, private
testing material or original game/campaign media without permission.

The PT-BR RC3 is a structural reference, **not a generic installer or media
library**. Its installer, plans, filenames and hashes are specific to PT-BR.
Renaming folders or disabling its checks does not make it suitable for your pack.
PT-BR text, voices and music are not generally licensed for redistribution in
another pack: see [the rights notice](../LICENSE-NOTICE.md).

A first pack does not need a custom installer or Python for installation. If you
later write an installer, preserve other locales and originals, validate baseline
and paths, record owned files, back up before replacement and support recovery.

## 10. Install, update and remove a pack

1. Close the game and other installers. Back up the test campaign's existing
   `localization/` outside the campaign and keep the previous pack.
2. Extract the language ZIP(s) into staging. Verify the author's file list/checksums
   and inspect the payload before copying it into the campaign.
3. Copy `payload/Reconquered Campaign/localization/fr/` into the test campaign's
   `localization/fr/`. Stop on unexpected conflicts. When updating, preserve the
   old files before replacing only those owned by this pack.
4. Merge the locale entry into `localization/locales.xml` if required, keeping all
   other languages. Do not install the `.example` file as a second registry.
5. Start compatible Claudius, select the language and campaign, and check the
   campaign picker, scenario screen, message text and narration.

The destination is
`<test-user-directory>/campaigns/Reconquered Campaign/localization/fr/`.
Do not create `Reconquered Campaign/Reconquered Campaign/` or put the extra
`payload/` wrapper inside the campaign.

To remove a pack, close the game, compare files with its list/hashes, remove only
unchanged pack-owned files and restore saved originals. Keep user-edited files
for review. Remove only your registry entry; do not roll back other languages
added after the backup. Never delete the whole campaign, saves or shared registry
to remove a language pack.

**A language-only ZIP is not a `.campaign` add-on mounted separately.** For private
packaged-campaign testing, insert the overlay into a copy of the complete campaign
ZIP. Its internal root must contain `Settings.xml`, `scenario/` and `localization/`
directly, without an extra wrapper. Use the `.campaign` extension. Do not
redistribute that complete campaign without permission. Begin with a directory;
packaged-campaign support is a separate test.

## 11. Validate before sharing

- Parse XML; check exact locale folders, scenario stems, UIDs and aliases. Syntax
  validation alone does not check the game schema, encoding, fonts or rendering.
- Check metadata keys and imperial guards against the exact campaign baseline.
- Check filenames/hashes for all media, and listen to the delivered recordings.
- Check selection, metadata, messages, large/body fonts and language changes.
  Verify fallback with a language for which the pack has no translation.
- Test briefing, events and victory: fanfare before narration, closing during
  fanfare/speech, and no sound leaking after leaving a message.
- Load an existing save in a copied profile. One successful load is not proof for
  all saves. Test folder and `.campaign` separately if both are advertised.
- Test installation/update/removal with another language already present;
  originals, saves and the other locale must remain intact.
- Publish OS, engine release/commit, campaign baseline, tested missions and known
  gaps. Automated checks do not replace full in-game linguistic/audiovisual QA.

If nothing loads, inspect the log for `Loaded custom message localization`,
`Loaded custom message media localization` and `Unable to load ...`. Check the
active user directory, selected campaign and exact `.mapx`/`.svx` filename stem.

### Technical reference

Checked against Claudius `26e050892` on 19 September 2026.
The [engine format reference](https://github.com/csfreitas/augustus/blob/26e0508921bcb1c01166fc683a59fb1917fa2426/doc/custom_campaign_localization.md)
contains additional examples and schema details. The [PT-BR coverage report](../TRANSLATION_COVERAGE.md)
and [QA checklist](../COMMUNITY_QA_CHECKLIST.md) illustrate scope/evidence tracking;
they do not validate a newly created translation.
