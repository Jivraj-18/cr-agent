# Clash Royale — what a player has to know (v1 knowledge pack)

Purpose: everything a human player keeps in their head during a 1v1 battle, written so that
(a) you can learn the game from it, and (b) it maps directly onto the agent's `get_state()`
fields and skills. Each section ends with **→ Agent needs** — what that knowledge turns into.

Status tags: **[verified]** = from official support pages / multiple sources (Nov 2026).
**[discover]** = must be measured on your phone in the discovery phase (pixels, tiles, timings).

---

## 1. How you win

- You destroy the opponent's towers. Each tower = 1 crown. Opponent has 2 Princess Towers
  (one per lane) and 1 King Tower in the middle. **[verified]**
- Destroy the King Tower → instant 3-crown win. **[verified]**
- Regular time is 3 minutes. If crowns are equal at the end → **2-minute overtime, sudden death**:
  the first tower destroyed wins. **[verified]**
- If still level after overtime → **tiebreaker**: all towers lose HP quickly, the side with the
  lowest-HP tower loses. Exactly equal → draw. **[verified]**

**Example.** It's 1–1 at 3:00. Overtime starts. Your Hog Rider takes their damaged left tower at
3:40 → you win immediately, even though you never touched the King.

**Cause → effect.** Because of the tiebreaker, *chip damage matters even if no tower falls*.
A tower at 300 HP is a liability in overtime even if it's "still standing".

**→ Agent needs:** `time_left`, `phase` (regular / overtime), `crowns_me`, `crowns_opp`,
`tower_hp[6]` (3 mine, 3 theirs). Tiebreaker logic: in overtime, protect your lowest tower.

---

## 2. Elixir — the only resource

- Start with 5 elixir, max 10. **[verified]**
- +1 elixir every 2.8 s (minutes 1–2). Rate doubles in minute 3 (1 per 1.4 s). Overtime:
  first minute x2, last minute x3. **[verified]**
- Every card costs elixir (1–9). You can't play a card you can't afford.
- At 10 elixir, generation stops → "leaking". Every second at 10 is free elixir thrown away.

**Example.** You sit at 10 elixir for 5.6 s waiting for the "perfect" play. You just lost
2 elixir — the opponent got 2 more plays' worth than you over the match.

**Cause → effect.** The opponent's elixir follows the *same* clock. If they just spent 9 elixir
on a big push, they are near 0 — that's when your counter-attack in the other lane is safest.

**→ Agent needs:** `elixir_me` (read from bar), `opp_elixir_estimate` (start 5, + clock,
− cost of every card they play, clamp 0–10), `elixir_rate` by phase. Rule: never sit at 10.

---

## 3. Cards: deck, hand, cycle

- Deck = 8 cards. Hand = 4 cards shown at the bottom, plus a small "next card" preview.
- When you play a card, the next card fills its slot. A played card comes back after 4 other
  cards have been played. **[verified]**
- Card types: **troops** (walk/fly and fight), **spells** (instant effect anywhere: Fireball,
  Arrows, Zap, The Log…), **buildings** (stationary; defend or spawn), and the **tower troop**
  that sits on your Princess Towers. **[verified]**
- **Win conditions** = cards whose job is to hit towers: building-only targeters (Hog Rider,
  Giant, Golem, Royal Giant) plus Goblin Barrel and Miner (can be placed anywhere). **[verified]**
- Advanced (ignore in v1): Champions (have an activated ability), Evolutions (upgraded versions
  of some cards with extra effects).

**Example.** Opponent plays Hog Rider. They now need to play 4 other cards before Hog Rider is
back. If you've counted 2 of those since, you know you have time before the next Hog arrives.

**→ Agent needs:** `hand[4]` (card id + playable?), `next_card`, `my_cycle` (order of my deck),
`opp_seen_cards` (up to 8), `opp_cycle_position` (which of their cards *can't* be in hand now).

---

## 4. What every unit is (static stats — no vision needed)

For every card the static data gives: elixir cost, hitpoints, damage, hit speed (→ DPS),
range (tiles), move speed, **targets** (ground / air / buildings-only), single-target vs
**splash**, count (how many units spawn), flying or ground, deploy time.

Source: RoyaleAPI `cr-api-data` (static JSON) + card wiki pages. Stats change with balance
updates → refresh this file periodically.

**Examples of why each field matters:**
- *Targets:* Minions fly. A Knight (ground melee) can't hit them. Defend with something that
  targets air (Musketeer, Archers, Arrows).
- *Splash vs single:* Skeleton Army (many tiny units) beats a single-target tank, dies to one
  splash hit (Valkyrie, Arrows, The Log).
- *Buildings-only:* Hog Rider ignores your troops and runs straight at the nearest building —
  so a cheap building can drag it away from your tower.
- *Range:* a unit with range 6 hits from behind a tank; a melee unit with range ~1 must walk up.

**→ Agent needs:** `cards.json` loaded at start; helper functions `can_hit(attacker, target)`,
`dps(card, level)`, `is_splash(card)`, `counters(threat)` → ranked list of cards in my hand
that can deal with it, cheapest first.

---

## 5. The arena (geometry)

- Portrait screen. Your side at the bottom, theirs at top. A **river** in the middle crossed by
  **two bridges** → two **lanes** (left, right). **[verified]**
- The arena is a tile grid. Players describe placements in tiles ("4-3 Cannon" = 4 tiles from
  the river, 3 tiles from the Princess Tower — the classic anti-Hog spot). **[verified concept,
  exact pixel↔tile mapping: discover]**
- You may deploy troops/buildings only on your own half. When you destroy an enemy Princess
  Tower, your deploy zone grows into that lane on their side. Spells (and Miner / Goblin Barrel)
  can go anywhere. **[discover exact zones]**
- **King Tower activation:** the King Tower starts asleep. It wakes up when one of its Princess
  Towers is destroyed or the King itself takes damage. Awake King = an extra cannon for the rest
  of the match. **[verified]**

**Cause → effect.** If your Fireball splashes their King early, you just gave them a free
third defensive tower. Conversely, players deliberately *pull* enemy troops (e.g. with Tornado)
into their own King to wake it up.

**→ Agent needs:** `tile_to_px(x, y)` and `px_to_tile(px, py)` calibration for the Moto G96
screen; `legal_deploy(card, tile)`; constants for bridge tiles, tower positions, river row;
`king_active_me`, `king_active_opp`.

---

## 6. How units move and pick targets

- Troops walk down their lane toward the nearest enemy target they are allowed to attack.
- Building-only troops go for the nearest building — a building placed in the middle can pull
  them off-lane ("pulling", "kiting").
- Once a troop is attacking something, it usually keeps attacking it until it dies; some spells
  (Zap, The Log, freeze/stun effects) interrupt and reset that.
- Placing a unit *behind your King Tower* means it takes several seconds to reach the bridge —
  time in which you regain elixir to add support. **[verified as standard advice]**

**Example.** Hog Rider crosses the bridge heading to your right tower. You drop a Cannon at 4-3
in the centre. The Hog now targets the Cannon instead, walks into range of *both* your Princess
Towers, and dies having done no tower damage. You spent 3 elixir vs their 4 → +1 for you.

**→ Agent needs:** track each enemy unit as `{card, x, y, lane, hp_est, target_guess}`;
time-to-reach-tower estimates from speed + distance (to decide *when* to place a defence).

---

## 7. Elixir trades — the core of the strategy

- **Positive trade:** you stop their attack spending less elixir than they did. Official example:
  The Log (2) on Goblin Barrel (3) = +1 for you. **[verified]**
- **Counter-push:** defenders that survive keep walking into the enemy side. Defending well
  *is* your next attack, at no extra cost.
- **Don't overcommit:** dumping all elixir into one push leaves you defenceless against their
  reply in the other lane.
- **Cycle in the back:** if nothing is happening, play a cheap card far back to avoid leaking
  and to bring your win condition back sooner.

**Example.** They play Giant (5) + Musketeer (4) = 9. You defend with Mini P.E.K.K.A (4) +
Skeletons (1) = 5. You're +4, they're near empty, and your Mini P.E.K.K.A survives → drop
your Hog Rider next to it at the bridge. That's a counter-push.

**→ Agent needs:** an `elixir_balance` running counter (my spent vs their spent on each
exchange); skill `counter_push()` triggered when my defenders survive and `opp_elixir_estimate`
is low.

---

## 8. Reading the opponent

- Over the first minute you see most of their 8 cards. Group them into an **archetype**:
  *Beatdown* (big tank like Golem/Giant + support — slow, heavy pushes), *Cycle* (cheap cards,
  Hog Rider/Miner, attack often), *Siege* (X-Bow/Mortar — buildings that shoot towers from your
  side), *Bait* (many small units so your one splash spell can't cover all), *Control*
  (defend, then chip with spells).
- Remember which spell they have. If they have Fireball, don't stack your support units in one
  clump.

**→ Agent needs:** `opp_archetype_guess`, `opp_spells_seen`, `opp_win_condition`.

---

## 9. Match phases — the plan changes with the clock

| Phase | Elixir | What players do |
|---|---|---|
| 0:00–~0:30 | x1 | Don't rush. Play a cheap card in the back, see what they have. |
| until 2:00 | x1 | Defend efficiently, positive trades, punish when they overspend. |
| 2:00–3:00 | x2 | Bigger pushes, two-lane pressure, keep spending (bar fills in 14 s). |
| Overtime | x2 → x3 | First tower wins. Protect your weakest tower, go for their weakest. |

**→ Agent needs:** `phase` drives which skills are allowed and how aggressive thresholds are.

---

## 10. The decision a player makes every ~1 second

```
1. THREAT?   An enemy unit is on my side / heading to a tower?
             → choose cheapest card in hand that counters it, place it at the right tile, NOW.
2. OPPORTUNITY?  Opponent just overspent (est. elixir low) or my defenders survived?
             → counter-push / attack the other lane.
3. LEAKING?  My elixir ≥ 9 and nothing to do?
             → cycle a cheap card behind the King Tower, or start a push from the back.
4. Otherwise wait and build elixir.
```

This loop is what the fast script runs. The LLM's job is *not* to run this loop — it is to
tune it: which cards count as counters, thresholds, placement tiles, and archetype-specific
adjustments, between matches or on big events.

---

## 11. Proposed `get_state()` (v1)

```json
{
  "t": 87.4, "phase": "x1", "time_left": 92,
  "elixir_me": 6, "opp_elixir_est": 3.2,
  "hand": [{"card":"hog_rider","cost":4},{"card":"the_log","cost":2},
           {"card":"cannon","cost":3},{"card":"musketeer","cost":4}],
  "next_card": "skeletons",
  "towers": {"me":{"left":1450,"king":2400,"right":900},
             "opp":{"left":1450,"king":2400,"right":1450}},
  "king_active": {"me": false, "opp": false},
  "enemy_units": [{"card":"giant","tile":[3,18],"lane":"left","hp_frac":0.9}],
  "my_units":    [{"card":"knight","tile":[4,12],"lane":"left"}],
  "opp_seen": ["giant","musketeer","fireball"], "opp_archetype": "beatdown?"
}
```

## 12. Things v1 deliberately ignores

Champions' abilities, Evolutions, card levels/King level differences, 2v2, special event rules,
emotes. Add later once the basic loop works in Training Camp.

---

### Sources
- Official elixir rules: support.clashroyale.com — "Elixir"
- Official 1v1 battle page (positive trades, card cycle, win conditions): support.clashroyale.com — "1v1 Battle"
- Overtime / tiebreaker / King activation: Wikipedia "Clash Royale"; Supercell dev post on tiebreakers (2019)
- Placement notation (4-3): trophycoach.com arena simulator
- Static card stats: github.com/RoyaleAPI/cr-api-data
- Prior bots to reuse for perception: github.com/wty-yy/katacr, github.com/Pbatch/ClashRoyaleBuildABot
