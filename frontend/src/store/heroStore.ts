import create from "zustand";

interface HeroState {
  currentHero:
    | "hero1"
    | "hero2"
    | "hero3"
    | "hero4"
    | "hero5"
    | "hero6"
    | "map";
  setCurrentHero: (
    hero: "hero1" | "hero2" | "hero3" | "hero4" | "hero5" | "hero6" | "map"
  ) => void;
}

export const useHeroStore = create<HeroState>((set) => ({
  currentHero: "hero1",
  setCurrentHero: (hero) => set({ currentHero: hero }),
}));
