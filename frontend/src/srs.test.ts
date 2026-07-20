import { describe, expect, it } from "vitest";
import { type CardState, dueQueue, isDue, newCardState, review } from "./srs";

const TODAY = "2026-07-20";

describe("FSRS scheduler", () => {
  it("first review initializes stability/difficulty and schedules ahead", () => {
    const s = review(newCardState("x", TODAY), "good", TODAY);
    expect(s.reps).toBe(1);
    expect(s.stability).toBeGreaterThan(0);
    expect(s.difficulty).toBeGreaterThanOrEqual(1);
    expect(s.difficulty).toBeLessThanOrEqual(10);
    expect(s.due > TODAY).toBe(true);
  });

  it("easier grades yield longer first intervals than harder ones", () => {
    const again = review(newCardState("x", TODAY), "again", TODAY);
    const hard = review(newCardState("x", TODAY), "hard", TODAY);
    const good = review(newCardState("x", TODAY), "good", TODAY);
    const easy = review(newCardState("x", TODAY), "easy", TODAY);
    expect(again.due <= hard.due).toBe(true);
    expect(hard.due <= good.due).toBe(true);
    expect(good.due <= easy.due).toBe(true);
  });

  it("successful reviews grow stability over time", () => {
    let s = review(newCardState("x", TODAY), "good", TODAY);
    const s1 = s.stability;
    s = review(s, "good", s.due); // review again when due
    expect(s.stability).toBeGreaterThan(s1);
  });

  it("'again' counts a lapse and does not increase stability", () => {
    let s = review(newCardState("x", TODAY), "good", TODAY);
    s = review(s, "good", s.due);
    const before = s.stability;
    s = review(s, "again", s.due);
    expect(s.lapses).toBe(1);
    expect(s.stability).toBeLessThanOrEqual(before);
  });

  it("difficulty stays within [1, 10] under repeated hard grades", () => {
    let s: CardState = newCardState("x", TODAY);
    let day = TODAY;
    for (let i = 0; i < 12; i++) {
      s = review(s, "again", day);
      day = s.due;
      expect(s.difficulty).toBeGreaterThanOrEqual(1);
      expect(s.difficulty).toBeLessThanOrEqual(10);
    }
  });

  it("isDue is true for a new card and false once scheduled ahead", () => {
    const fresh = newCardState("x", TODAY);
    expect(isDue(fresh, TODAY)).toBe(true);
    const later = review(fresh, "easy", TODAY);
    expect(isDue(later, TODAY)).toBe(false);
  });

  it("dueQueue returns only new/due cards", () => {
    const store = { seen: review(newCardState("seen", TODAY), "good", TODAY) };
    expect(dueQueue(store, ["seen", "fresh"], TODAY)).toEqual(["fresh"]);
  });
});
