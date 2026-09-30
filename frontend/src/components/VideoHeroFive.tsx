import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import video5 from "../assets/5.mp4";
import video6 from "../assets/6.mp4";
import { useHeroStore } from "../store/heroStore";
import VideoPreloader from "./VideoPreloader";

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

export default function VideoHeroFive() {
  const { setCurrentHero } = useHeroStore();
  const [currentPart, setCurrentPart] = useState(1);
  const heroRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const partOneRef = useRef<HTMLDivElement>(null);
  const partTwoRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);
  const backButtonRef = useRef<HTMLButtonElement>(null);
  const mapButtonRef = useRef<HTMLButtonElement>(null);

  // Initial animation on mount
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set(overlayRef.current, { opacity: 0 });
      gsap.set(titleRef.current, { opacity: 0, y: 30 });
      gsap.set(partOneRef.current, { opacity: 0, y: 30 });
      gsap.set(partTwoRef.current, { opacity: 0, y: 30 });
      gsap.set(
        [nextButtonRef.current, backButtonRef.current, mapButtonRef.current],
        {
          opacity: 0,
          x: 30,
          y: 20,
        }
      );

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

      // Animate current part content
      if (currentPart === 1 && partOneRef.current) {
        tl.to(
          partOneRef.current,
          { opacity: 1, y: 0, duration: 1, ease: "power2.out" },
          "-=0.3"
        );
      } else if (currentPart === 2 && partTwoRef.current) {
        tl.to(
          partTwoRef.current,
          { opacity: 1, y: 0, duration: 1, ease: "power2.out" },
          "-=0.3"
        );
      }

      // Animate buttons based on current part
      const buttonsToAnimate =
        currentPart === 1
          ? [nextButtonRef.current]
          : [mapButtonRef.current, backButtonRef.current];

      // Filter out null buttons
      const validButtons = buttonsToAnimate.filter((button) => button !== null);

      if (validButtons.length > 0) {
        tl.to(
          validButtons,
          { opacity: 1, x: 0, y: 0, duration: 0.8, ease: "back.out(1.7)" },
          "-=0.4"
        );
      }
    }, heroRef);

    return () => ctx.revert();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle part switching animations
  useEffect(() => {
    if (currentPart === 1) {
      // Animate part 1 in
      if (partOneRef.current) {
        gsap.fromTo(
          partOneRef.current,
          { opacity: 0, y: 30 },
          { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }
        );
      }
      // Animate next button in
      if (nextButtonRef.current) {
        gsap.fromTo(
          nextButtonRef.current,
          { opacity: 0, x: 30, y: 20 },
          { opacity: 1, x: 0, y: 0, duration: 0.6, ease: "back.out(1.7)" }
        );
      }
    } else if (currentPart === 2) {
      // Animate part 2 in
      if (partTwoRef.current) {
        gsap.fromTo(
          partTwoRef.current,
          { opacity: 0, y: 30 },
          { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }
        );
      }
      // Animate map and back buttons in
      if (mapButtonRef.current) {
        gsap.fromTo(
          mapButtonRef.current,
          { opacity: 0, x: 30, y: 20 },
          { opacity: 1, x: 0, y: 0, duration: 0.6, ease: "back.out(1.7)" }
        );
      }
      if (backButtonRef.current) {
        gsap.fromTo(
          backButtonRef.current,
          { opacity: 0, x: 30, y: 20 },
          {
            opacity: 1,
            x: 0,
            y: 0,
            duration: 0.6,
            ease: "back.out(1.7)",
            delay: 0.1,
          }
        );
      }
    }
  }, [currentPart]);

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

  return (
    <div ref={heroRef} className="relative w-full h-screen overflow-hidden">
      {/* Video Background */}
      <video
        src={video5}
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Buffer the next chapter's video ahead of time for an instant transition */}
      <VideoPreloader src={video6} />

      {/* Overlay */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-gradient-to-br from-blue-900/80 via-teal-900/70 to-cyan-900/80"
      />

      {/* Back Button - Top Left */}
      <div className="absolute top-6 left-6 z-20">
        <button
          onClick={() => setCurrentHero("hero4")}
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
            Back to Scent of Life
          </span>
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center h-full px-8">
        <div className="max-w-4xl mx-auto text-center">
          {/* Main Title */}
          <h1
            ref={titleRef}
            className="text-3xl md:text-4xl font-bold text-white mb-6 leading-tight"
            style={{
              textShadow: "2px 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            The Hunt Revealed
          </h1>

          {/* Part 1 */}
          {currentPart === 1 && (
            <div ref={partOneRef} className="mb-8">
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                  A Predicted Hotspot
                </h2>
                <p className="text-lg md:text-xl text-white/90 leading-relaxed">
                  The data was right! A warm East Australian Current eddy
                  meeting a phytoplankton bloom off the New South Wales coast
                  created exactly the hunting ground the model predicted.
                </p>
              </div>
            </div>
          )}

          {/* Part 2 */}
          {currentPart === 2 && (
            <div ref={partTwoRef} className="mb-8">
              <div className="bg-gradient-to-r from-emerald-500/20 to-teal-500/20 backdrop-blur-md rounded-2xl p-6 border border-emerald-400/30 shadow-2xl">
                <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                  Why Her Hunt Matters
                </h2>
                <p className="text-lg md:text-xl text-white/90 leading-relaxed">
                  As an apex predator, Sharko's hunt keeps Australia's marine
                  ecosystems in balance — removing the sick and weak protects
                  fish and seal populations from disease and overpopulation.
                  Great White Sharks have been fully protected under Australian
                  law since the 1990s: a healthy Australian coast needs sharks
                  like her.
                </p>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            {currentPart === 1 && (
              <button
                ref={nextButtonRef}
                className="group relative overflow-hidden bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:via-teal-500 hover:to-cyan-500 text-white px-12 py-4 text-lg font-semibold rounded-full shadow-2xl transition-all duration-500 transform hover:scale-105 hover:shadow-emerald-500/25 hover:cursor-pointer"
                onMouseEnter={() => handleButtonHover(true, nextButtonRef)}
                onMouseLeave={() => handleButtonHover(false, nextButtonRef)}
                onClick={() => setCurrentPart(2)}
              >
                <span className="relative z-10 flex items-center gap-3">
                  Next
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
              </button>
            )}

            {currentPart === 2 && (
              <>
                <button
                  ref={mapButtonRef}
                  className="group relative overflow-hidden bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:via-teal-500 hover:to-cyan-500 text-white px-12 py-4 text-lg font-semibold rounded-full shadow-2xl transition-all duration-500 transform hover:scale-105 hover:shadow-emerald-500/25 hover:cursor-pointer"
                  onMouseEnter={() => handleButtonHover(true, mapButtonRef)}
                  onMouseLeave={() => handleButtonHover(false, mapButtonRef)}
                  onClick={() => setCurrentHero("hero6")}
                >
                  <span className="relative z-10 flex items-center gap-3">
                    <svg
                      className="w-6 h-6"
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
                    From Prediction to Protection
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
                </button>

                <button
                  ref={backButtonRef}
                  className="group relative overflow-hidden bg-white/10 hover:bg-white/20 text-white px-8 py-4 text-lg font-semibold rounded-full border border-white/30 shadow-xl transition-all duration-500 transform hover:scale-105 hover:cursor-pointer"
                  onMouseEnter={() => handleButtonHover(true, backButtonRef)}
                  onMouseLeave={() => handleButtonHover(false, backButtonRef)}
                  onClick={() => setCurrentPart(1)}
                >
                  <span className="relative z-10 flex items-center gap-3">
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
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                    Back to Part 1
                  </span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
