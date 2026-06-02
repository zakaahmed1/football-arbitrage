import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  leagues: defineTable({
    id: v.string(),     // e.g. "premier"
    name: v.string(),   // "Premier League"
    sport: v.string(),  // "Football"
  })
    .index("by_sport", ["sport"])
    .index("by_customId", ["id"]), // renamed to avoid reserved "by_id"

  opportunities: defineTable({
    id: v.string(),           // e.g. "arb1"
    homeTeam: v.string(),
    awayTeam: v.string(),
    startTime: v.string(),    // ISO string
    sport: v.string(),
    leagueId: v.string(),     // foreign key to leagues.id
    profitPercent: v.number(),
    odds: v.array(
      v.object({
        bookmaker: v.string(),
        market: v.string(),
        odds: v.number(),
      })
    ),
  })
    .index("by_sport", ["sport"])
    .index("by_leagueId", ["leagueId"])
    .index("by_startTime", ["startTime"]),
});
