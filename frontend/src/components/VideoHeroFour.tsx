"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import video4 from "../assets/4.mp4";
import video5 from "../assets/5.mp4";
import { useHeroStore } from "../store/heroStore";
import VideoPreloader from "./VideoPreloader";

// Helper function to split text into characters and wrap them in spans
const splitTextIntoChars = (element: HTMLElement | null) => {
  if (!element) return [];

  const text = element.textContent || "";
  element.innerHTML = "";

  const chars = text.split("").map((char) => {
    const span = document.createElement("span");
    span.textContent = char === " " ? "\u00A0" : char; // Use non-breaking space for actual spaces
    span.style.display = "inline-block";
    span.style.opacity = "0";
    span.style.transform = "translateY(20px)";
    element.appendChild(span);
    return span;
  });

  return chars;
};

export default function VideoHeroFour() {
  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const infoCardRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const backButtonRef = useRef<HTMLButtonElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const { setCurrentHero } = useHeroStore();

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([buttonRef.current, backButtonRef.current], {
        opacity: 0,
        x: 100,
        y: 30,
      });

      gsap.set(overlayRef.current, {
        opacity: 0,
      });

      // Split text - characters for title only
      const titleChars = splitTextIntoChars(titleRef.current);

      // Set initial state for subtitle and info card
      gsap.set([subtitleRef.current, infoCardRef.current], {
        opacity: 0,
        y: 20,
      });

      // Create timeline for reveal animations
      const tl = gsap.timeline({ delay: 0.5 });

      // Fade in overlay
      tl.to(overlayRef.current, {
        opacity: 1,
        duration: 1,
        ease: "power2.out",
      });

      // Animate title characters
      tl.to(
        titleChars,
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: "power3.out",
          stagger: 0.05, // 50ms delay between each character
        },
        "-=0.5"
      );

      // Animate subtitle with simple fade in
      tl.to(
        subtitleRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 1,
          ease: "power2.out",
        },
        "-=0.3"
      );

      // Animate info card with slide in effect
      tl.to(
        infoCardRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 1,
          ease: "power2.out",
        },
        "-=0.2"
      );

      // Animate buttons
      tl.to(
        [buttonRef.current, backButtonRef.current],
        {
          opacity: 1,
          x: 0,
          y: 0,
          duration: 0.8,
          ease: "back.out(1.7)",
        },
        "-=0.4"
      );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  const handleButtonHover = (isHovering: boolean) => {
    gsap.to(buttonRef.current, {
      scale: isHovering ? 1.05 : 1,
      duration: 0.3,
      ease: "power2.out",
    });

    // Add a subtle glow effect
    gsap.to(buttonRef.current, {
      boxShadow: isHovering
        ? "0 20px 40px rgba(59, 130, 246, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.1)"
        : "0 10px 25px rgba(0, 0, 0, 0.2)",
      duration: 0.3,
      ease: "power2.out",
    });
  };

  return (
    <div ref={heroRef} className="relative h-screen w-full overflow-hidden">
      <video
        className="absolute inset-0 h-full w-full object-cover"
        style={{ filter: "brightness(0.7)" }}
        autoPlay
        loop
        muted
        playsInline
      >
        <source src={video4} type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Buffer the next chapter's video ahead of time for an instant transition */}
      <VideoPreloader src={video5} />

      {/* Dark Overlay for Better Text Readability */}
      {/* <div ref={overlayRef} className="absolute inset-0 bg-black/40" /> */}

      {/* Back Button - Top Left */}
      <div className="absolute top-6 left-6 z-20">
        <button
          onClick={() => setCurrentHero("hero3")}
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
            Back to Journey Pattern
          </span>
        </button>
      </div>

      {/* Content Overlay */}
      <div className="relative z-10 flex h-full items-center justify-end px-8 md:px-16 lg:px-24 ">
        <div className="max-w-4xl mr-10">
          {/* Decorative Line */}
          <div className="mb-8 ml-auto h-1 w-24 bg-gradient-to-r from-blue-500 to-teal-500 rounded-full"></div>

          {/* Main Headline */}
          <h3
            ref={titleRef}
            className="mb-8 text-2xl font-extrabold leading-tight text-white md:text-3xl lg:text-4xl text-balance tracking-tight"
          >
            Clue #2: The Scent of Life
          </h3>

          {/* Subtitle */}
          <p
            ref={subtitleRef}
            className="mb-8 text-lg leading-relaxed text-gray-200 md:text-xl text-pretty max-w-lg ml-auto text-justify backdrop-blur-sm bg-black/40 p-6 rounded-lg font-light"
          >
            Where the East Australian Current meets cooler water off the New
            South Wales coast, nutrient-rich upwelling triggers phytoplankton
            blooms visible from space as swirls of green. Phytoplankton feed
            baitfish, baitfish draw the fur seal colonies of islands like
            Montague Island — and that's Sharko's prey.
          </p>

          {/* Information Card */}
          <div
            ref={infoCardRef}
            className="mb-12 max-w-lg ml-auto backdrop-blur-sm bg-gradient-to-r from-emerald-900/60 to-green-900/60 p-6 rounded-lg border border-emerald-400/30"
          >
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-emerald-400 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <svg
                  className="w-4 h-4 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h4 className="text-emerald-300 font-semibold mb-2 text-sm uppercase tracking-wide">
                  Ocean Food Web
                </h4>
                <p className="text-white text-sm leading-relaxed">
                  Phytoplankton → Baitfish → Seals → Sharko. This chain of
                  life, mapped with real satellite ocean-colour and
                  sea-surface-temperature data, drives every move she makes
                  along the Australian coast.
                </p>
              </div>
            </div>
          </div>

          {/* Call-to-Action Buttons */}
          <div className="flex flex-col items-end gap-4">
            <button
              ref={buttonRef}
              className="group relative overflow-hidden bg-gradient-to-r from-blue-600 via-teal-600 to-cyan-600 hover:from-blue-500 hover:via-teal-500 hover:to-cyan-500 text-white px-12 py-4 text-lg font-semibold rounded-full shadow-2xl transition-all duration-500 transform hover:scale-105 hover:shadow-blue-500/25 hover:cursor-pointer"
              onMouseEnter={() => handleButtonHover(true)}
              onMouseLeave={() => handleButtonHover(false)}
              onClick={() => setCurrentHero("hero5")}
            >
              {/* Button Background Effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>

              {/* Button Content */}
              <span className="relative z-10 flex items-center gap-3">
                View Interactive Map
                <svg
                  className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
