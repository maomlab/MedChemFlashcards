import { describe, expect, it } from "vitest";
import { dueQueue, getState, isDue, newCardState, review } from "./srs";

const TODAY = "2026-07-20";

describe("SM-2 scheduler", () => {
  it("first 'good' review schedules 1 day out", () => {
    const s = review(newCardState("x", TODAY), "good", TODAY);
    expect(s.reps).toBe(1);
    expect(s.intervalDays).toBe(1);
    expect(s.due).toBe("2026-07-21");
  });

  it("second 'good' review schedules 6 days out", () => {
    let s = review(newCardState("x", TODAY), "good", TODAY);
    s = review(s, "good", s.due);
    expect(s.reps).toBe(2);
    expect(s.intervalDays).toBe(6);
  });

  it("'again' is a lapse: resets reps, interval 1 day, increments lapses", () => {
    let s = review(newCardState("x", TODAY), "good", TODAY);
    s = review(s, "good", s.due);
    s = review(s, "again", s.due);
    expect(s.reps).toBe(0);
    expect(s.intervalDays).toBe(1);
    expect(s.lapses).toBe(1);
  });

  it("ease never drops below 1.3", () => {
    let s = newCardState("x", TODAY);
    for (let i = 0; i < 10; i++) s = review(s, "again", TODAY);
    expect(s.ease).toBeGreaterThanOrEqual(1.3);
  });

  it("isDue is true for a new card today and false once scheduled ahead", () => {
    const fresh = newCardState("x", TODAY);
    expect(isDue(fresh, TODAY)).toBe(true);
    const later = review(fresh, "easy", TODAY);
    expect(isDue(later, TODAY)).toBe(false);
  });

  it("dueQueue returns only new/due cards", () => {
    const store = { seen: review(newCardState("seen", TODAY), "good", TODAY) };
    const q = dueQueue(store, ["seen", "fresh"], TODAY);
    expect(q).toEqual(["fresh"]);
    expect(getState(store, "fresh", TODAY).reps).toBe(0);
  });
});
