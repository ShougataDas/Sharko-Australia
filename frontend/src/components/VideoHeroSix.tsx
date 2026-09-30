import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import video6 from "../assets/6.mp4";
import { useHeroStore } from "../store/heroStore";

const splitTextIntoChars = (element: HTMLElement | null) => {
  if (!element) return [];
  const text = element.textContent || "";
  element.innerHTML = "";
  const chars = text.split("").map((char) => {
    const span = document.createElement("span");
    span.textContent = char === " " ? "\u00A0" : char;
    span.style.display = "inline-block";
    span.style.opacity = "0";
    span.style.transform = "translateY(20px)";
    element.appendChild(span);
    return span;
  });
  return chars;
};

export default function VideoHeroSix() {
  const { setCurrentHero } = useHeroStore();
  const [activeTab, setActiveTab] = useState("fishermen");
  const heroRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const exploreButtonRef = useRef<HTMLButtonElement>(null);
  const backButtonRef = useRef<HTMLButtonElement>(null);

  const tabContent = {
    fishermen: {
      title: "For Fishermen",
      description:
        "Australian fisheries use real-time hotspot maps like this one to avoid areas with high shark activity, reducing accidental bycatch and saving both sharks and fishing gear.",
      icon: "🎣",
      color: "from-blue-500/20 to-cyan-500/20",
      borderColor: "border-blue-400/30",
    },
    conservationists: {
      title: "For Conservationists",
      description:
        "Researchers and policymakers use tracking data like Sharko's to help define Marine Protected Areas — such as the Great Barrier Reef and Ningaloo Marine Parks — that safeguard the habitats sharks need to feed and breed.",
      icon: "🌊",
      color: "from-emerald-500/20 to-teal-500/20",
      borderColor: "border-emerald-400/30",
    },
    public: {
      title: "For Public Safety",
      description:
        "NSW's real SharkSmart network turns satellite and acoustic tag detections into instant beach alerts, letting swimmers know when tagged sharks like Sharko are nearby — safety through awareness, not fear.",
      icon: "🏖️",
      color: "from-amber-500/20 to-orange-500/20",
      borderColor: "border-amber-400/30",
    },
  };

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set(overlayRef.current, { opacity: 0 });
      gsap.set(titleRef.current, { opacity: 0, y: 30 });
      gsap.set(contentRef.current, { opacity: 0, y: 30 });
      gsap.set(tabsRef.current, { opacity: 0, y: 30 });
      gsap.set([exploreButtonRef.current, backButtonRef.current], {
        opacity: 0,
        x: 30,
        y: 20,
      });

      // Create timeline
      const tl = gsap.timeline();

      // Animate overlay
      tl.to(overlayRef.current, {
        opacity: 0.7,
        duration: 1.5,
        ease: "power2.out",
      });

      // Animate title with character reveal
      const titleChars = splitTextIntoChars(titleRef.current);
      tl.to(
        titleChars,
        { opacity: 1, y: 0, duration: 0.8, ease: "power3.out", stagger: 0.05 },
        "-=0.5"
      );

      // Animate content
      tl.to(
        contentRef.current,
        { opacity: 1, y: 0, duration: 1, ease: "power2.out" },
        "-=0.3"
      );

      // Animate tabs
      tl.to(
        tabsRef.current,
        { opacity: 1, y: 0, duration: 1, ease: "power2.out" },
        "-=0.2"
      );

      // Animate buttons
      tl.to(
        [exploreButtonRef.current, backButtonRef.current],
        { opacity: 1, x: 0, y: 0, duration: 0.8, ease: "back.out(1.7)" },
        "-=0.4"
      );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  const handleButtonHover = (
    isHovering: boolean,
    buttonRef: React.RefObject<HTMLButtonElement>
  ) => {
    if (buttonRef.current) {
      gsap.to(buttonRef.current, {
        scale: isHovering ? 1.05 : 1,
        duration: 0.3,
        ease: "power2.out",
      });
    }
  };

  const handleTabClick = (tabKey: string) => {
    setActiveTab(tabKey);
  };

  return (
    <div ref={heroRef} className="relative w-full h-screen overflow-hidden">
      {/* Video Background */}
      <video
        src={video6}
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Overlay */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-gradient-to-br from-blue-900/80 via-teal-900/70 to-cyan-900/80"
      />

      {/* Back Button - Top Left */}
      <div className="absolute top-6 left-6 z-20">
        <button
          ref={backButtonRef}
          onClick={() => setCurrentHero("hero5")}
          className="group relative overflow-hidden bg-white/10 hover:bg-white/20 text-white px-6 py-3 text-sm font-medium rounded-full border border-white/30 shadow-lg transition-all duration-300 transform hover:scale-105 hover:cursor-pointer"
        >
          <span className="relative z-10 flex items-center gap-2">
            <svg
              className="w-4 h-4 transition-transform duration-300 group-hover:-translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 17l-5-5m0 0l5-5m-5 5h12"
              />
            </svg>
            Back to The Hunt Revealed
          </span>
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center h-full px-4">
        <div className="max-w-5xl mx-auto text-center">
          {/* Main Title */}
          <h1
            ref={titleRef}
            className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight"
            style={{
              textShadow: "2px 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            From Prediction to Protection
          </h1>

          {/* Main Content */}
          <div ref={contentRef} className="mb-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 shadow-2xl mb-4">
              <p className="text-lg md:text-xl text-white/90 leading-relaxed">
                This is where data changes the world. In New South Wales, the
                real SharkSmart program uses satellite tags just like Sharko's
                — plus listening stations along the coast — to turn shark
                science into decisions that keep Australia's waters safer for
                everyone.
              </p>
            </div>
          </div>

          {/* Interactive Tabs */}
          <div ref={tabsRef} className="mb-6">
            {/* Tab Navigation */}
            <div className="flex flex-wrap justify-center gap-2 mb-4">
              {Object.entries(tabContent).map(([key, content]) => (
                <button
                  key={key}
                  onClick={() => handleTabClick(key)}
                  className={`group relative overflow-hidden px-4 py-2 rounded-full border-2 transition-all duration-500 transform hover:scale-105 ${
                    activeTab === key
                      ? `${content.borderColor} bg-white/20 backdrop-blur-md`
                      : "border-white/30 bg-white/10 hover:bg-white/15"
                  }`}
                >
                  <span className="flex items-center gap-2 text-white font-semibold text-sm">
                    <span className="text-lg">{content.icon}</span>
                    {content.title}
                  </span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="max-w-3xl mx-auto">
              <div
                className={`bg-gradient-to-r ${
                  tabContent[activeTab as keyof typeof tabContent].color
                } backdrop-blur-md rounded-2xl p-4 border ${
                  tabContent[activeTab as keyof typeof tabContent].borderColor
                } shadow-2xl`}
              >
                <h3 className="text-xl md:text-2xl font-bold text-white mb-3 flex items-center justify-center gap-3">
                  <span className="text-2xl">
                    {tabContent[activeTab as keyof typeof tabContent].icon}
                  </span>
                  {tabContent[activeTab as keyof typeof tabContent].title}
                </h3>
                <p className="text-base md:text-lg text-white/90 leading-relaxed">
                  {tabContent[activeTab as keyof typeof tabContent].description}
                </p>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <button
              ref={exploreButtonRef}
              className="group relative overflow-hidden bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:via-teal-500 hover:to-cyan-500 text-white px-8 py-3 text-base font-semibold rounded-full shadow-2xl transition-all duration-500 transform hover:scale-105 hover:shadow-emerald-500/25 hover:cursor-pointer"
              onMouseEnter={() => handleButtonHover(true, exploreButtonRef)}
              onMouseLeave={() => handleButtonHover(false, exploreButtonRef)}
              onClick={() => setCurrentHero("map")}
            >
              <span className="relative z-10 flex items-center gap-2">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                  />
                </svg>
                Explore Australia's Hotspots
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
