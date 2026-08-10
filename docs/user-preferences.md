# User preferences

Every registered user receives a persistent `UserPreference` row. `GET /api/preferences` retrieves it and `PUT /api/preferences` replaces all controlled fields. Both require an access token.

## Controlled fields

- `preferred_genres`: values from the AI `genres` taxonomy.
- `preferred_platforms`: values from `platforms`.
- `preferred_modes`: values from `modes`.
- `preferred_moods`: values from `moods`.
- `preferred_difficulty`: `easy`, `medium`, `hard`, or null.
- `price_preference`: `free`, `paid`, or null.
- `hardware_level`: `low-end`, `mid-range`, `high-end`, or null.

List inputs reject unknown values, remove duplicates, and return values in authoritative taxonomy order. The frontend options mirror `backend/app/ai/taxonomy.py`.

`PreferenceValues.to_ai_preferences()` exposes the profile as the existing immutable `ExtractedPreferences` representation (`genres`, `platforms`, `modes`, `moods`, `difficulty`, `price_type`, and `hardware_level`). The Phase 12 personalisation service consumes that normalized boundary as its explicit-preference signal. Its influence is bounded to the configured preference budget and reduced when the active prompt already expresses the same category.

```json
{
  "preferred_genres": ["action", "strategy"],
  "preferred_platforms": ["PC"],
  "preferred_modes": ["single-player", "offline"],
  "preferred_moods": ["relaxing"],
  "preferred_difficulty": "medium",
  "price_preference": "paid",
  "hardware_level": "mid-range"
}
```
