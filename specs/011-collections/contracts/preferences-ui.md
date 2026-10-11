# Contract: Preferences UI and Setting

## GSettings key

```xml
<key name="hidden-games-in-collections" type="b">
  <default>false</default>
</key>
```

Added to the main schema in `data/page.samuelm333.Cartridges.gschema.xml.in`. Writing the key from anywhere (the Preferences switch, `gsettings set`) takes effect in a running app at once.

## General page, Behavior group

```text
Behavior
+-----------------------------------------------------------+
| Exit After Launching Games                          [o  ] |
| Cover Image Launches Game                           [o  ] |
| Swaps the behavior of the cover image and ...             |
| Hidden games show in Collections                    [o  ] |   <- new
| Useful for hiding launchers and tools                     |
+-----------------------------------------------------------+
```

| Widget | Blueprint ID | Behavior |
|--------|--------------|----------|
| `Adw.SwitchRow` | `hidden_games_in_collections_switch` | Title "Hidden games show in Collections"; `subtitle` "Useful for hiding launchers and tools"; no tooltip. Bound two ways to `hidden-games-in-collections` by `_bind_switches` (the attribute name is the key with `-` turned into `_`, plus `_switch`). |

The title and subtitle are translatable. The row is visible in every build and on every platform.
