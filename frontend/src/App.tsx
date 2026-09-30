import "./App.css";
import VideoHero from "./components/VideoHero";
import VideoHeroTwo from "./components/VideoHeroTwo";
import VideoHeroThree from "./components/VideoHeroThree";
import VideoHeroFour from "./components/VideoHeroFour";
import VideoHeroFive from "./components/VideoHeroFive";
import VideoHeroSix from "./components/VideoHeroSix";
import { useHeroStore } from "./store/heroStore";

import Mapbox from "./components/Mapbox";
export default function App() {
  const { currentHero } = useHeroStore();

  const renderHero = () => {
    switch (currentHero) {
      case "hero1":
        return <VideoHero />;
      case "hero2":
        return <VideoHeroTwo />;
      case "hero3":
        return <VideoHeroThree />;
      case "hero4":
        return <VideoHeroFour />;
      case "hero5":
        return <VideoHeroFive />;
      case "hero6":
        return <VideoHeroSix />;
      case "map":
        return <Mapbox />;
      default:
        return <VideoHero />;
    }
  };

  return <>{renderHero()}</>;
}
