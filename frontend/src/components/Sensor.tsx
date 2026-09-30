"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import DataFlow from "./DataFlow";

export function SensorDiagram() {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contentRef.current) return;

    // Register GSAP plugins once
    if (
      !(
        gsap as unknown as {
          core?: { globals?: () => { ScrollTrigger?: unknown } };
        }
      ).core?.globals?.()?.ScrollTrigger
    ) {
      gsap.registerPlugin(ScrollTrigger);
    }

    gsap.fromTo(
      contentRef.current.children,
      { opacity: 0, y: 40, rotateX: -15 },
      {
        opacity: 1,
        y: 0,
        rotateX: 0,
        duration: 1,
        stagger: 0.12,
        delay: 0.3,
        ease: "power3.out",
      }
    );

    const lines = document.querySelectorAll(".connection-line");
    lines.forEach((line) => {
      gsap.fromTo(
        line,
        { scaleY: 0, transformOrigin: "top" },
        {
          scaleY: 1,
          duration: 0.8,
          delay: 1,
          ease: "power2.out",
        }
      );
    });

    const particles = document.querySelectorAll(".particle");
    particles.forEach((particle, i) => {
      gsap.fromTo(
        particle,
        { y: 0, opacity: 0 },
        {
          y: 80,
          opacity: 1,
          duration: 2,
          delay: 1.5 + i * 0.3,
          repeat: -1,
          ease: "none",
          onRepeat: () => {
            gsap.set(particle, { opacity: 0 });
            gsap.to(particle, { opacity: 1, duration: 0.3 });
          },
        }
      );
    });

    const modules = document.querySelectorAll(".module-card");
    gsap.to(modules, {
      boxShadow: "0 0 30px rgba(59, 130, 246, 0.3)",
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      stagger: 0.4,
    });

    const arrows = document.querySelectorAll(".flow-arrow");
    gsap.to(arrows, {
      y: 10,
      scale: 1.1,
      duration: 1.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      stagger: 0.2,
    });

    const packets = document.querySelectorAll(".data-packet");
    packets.forEach((packet) => {
      gsap.to(packet, {
        backgroundPosition: "200% center",
        duration: 2.5,
        repeat: -1,
        ease: "none",
      });

      gsap.to(packet, {
        borderColor: "rgba(139, 92, 246, 0.6)",
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    });

    const decisionBoxes = document.querySelectorAll(".decision-box");
    decisionBoxes.forEach((box) => {
      gsap.to(box, {
        borderColor: "rgba(168, 85, 247, 0.4)",
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    });

    const confirmed = document.querySelectorAll(".confirmed-state");
    confirmed.forEach((el) => {
      gsap.to(el, {
        boxShadow:
          "0 0 25px rgba(16, 185, 129, 0.5), inset 0 0 15px rgba(16, 185, 129, 0.1)",
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    });

    const stageNumbers = document.querySelectorAll(".stage-number");
    gsap.to(stageNumbers, {
      scale: 1.05,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      stagger: 0.3,
    });

    // Scroll-triggered reveal animations for cards/divs
    const revealTargets: Element[] = Array.from(
      contentRef.current.querySelectorAll(
        ".glass-card, .module-card, .decision-box, .confirmed-state, .data-packet, .content-card"
      )
    );

    revealTargets.forEach((el, idx) => {
      const direction = idx % 3; // 0: left->right, 1: right->left, 2: up reveal
      const fromX = direction === 0 ? -40 : direction === 1 ? 40 : 0;
      const fromY = direction === 2 ? 30 : 0;

      gsap.fromTo(
        el,
        { opacity: 0, x: fromX, y: fromY, filter: "blur(6px)" },
        {
          opacity: 1,
          x: 0,
          y: 0,
          filter: "blur(0px)",
          duration: 0.9,
          ease: "power3.out",
          scrollTrigger: {
            trigger: el,
            start: "top 85%",
            end: "top 40%",
            toggleActions: "play none none reverse",
          },
        }
      );
    });
  }, []);

  return (
    <div className="min-h-screen w-full overflow-y-auto  bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-8 py-16">
        {/* Content */}
        <div ref={contentRef}>
          {/* Title with Description */}
          <div className="text-center space-y-6 mb-16">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent tracking-tight">
              Smart Fusion Metabolic Kill Tag
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
              An advanced biotelemetry system combining inertial measurement
              units (IMU) and pH sensors to detect and confirm predation events
              in marine environments. The SF-MKT uses AI-powered pattern
              recognition to distinguish true predation from false positives,
              transmitting critical data via satellite for real-time marine
              ecosystem monitoring.
            </p>
            <div className="flex items-center justify-center gap-8 text-sm text-slate-400 pt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-cyan-500/60 shadow-lg shadow-cyan-500/50" />
                <span>External Module</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500/60 shadow-lg shadow-orange-500/50" />
                <span>Internal Module</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500/60 shadow-lg shadow-purple-500/50" />
                <span>Data Flow</span>
              </div>
            </div>
          </div>

          {/* Section 1: System Architecture */}
          <div className="glass-card rounded-2xl p-8 border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl">
            <h2 className="text-2xl font-semibold text-blue-300 mb-8 tracking-wide">
              1. System Architecture
            </h2>
            <div className="space-y-0">
              {/* External Module */}
              <div className="module-card bg-gradient-to-br from-cyan-900/40 via-blue-900/30 to-slate-900/40 backdrop-blur-sm rounded-xl p-6 border border-cyan-500/30 mb-6 shadow-lg shadow-cyan-500/20">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-400/40 flex items-center justify-center text-xs font-bold text-cyan-300 shadow-inner shadow-cyan-500/20">
                    EXT
                  </div>
                  <div>
                    <div className="text-base font-semibold text-cyan-100">
                      External Module
                    </div>
                    <div className="text-xs text-cyan-400/70 mt-0.5">
                      Dorsal Fin Mount
                    </div>
                  </div>
                </div>
                <ul className="space-y-2 list-none text-sm text-slate-300">
                  <li className="pl-4 border-l-2 border-cyan-500/40 py-1">
                    Main Battery (Li-ion)
                  </li>
                  <li className="pl-4 border-l-2 border-cyan-500/40 py-1">
                    Microcontroller (AI Processor)
                  </li>
                  <li className="pl-4 border-l-2 border-cyan-500/40 py-1">
                    Fastloc-GPS & Argos Modem
                  </li>
                  <li className="pl-4 border-l-2 border-cyan-500/40 py-1">
                    IMU (9-axis){" "}
                    <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-medium ml-2 border border-cyan-400/30">
                      TRIGGER
                    </span>
                  </li>
                  <li className="pl-4 border-l-2 border-cyan-500/40 py-1">
                    Data Storage & Processing
                  </li>
                </ul>
              </div>

              {/* Connection line with particles */}
              <div className="flex justify-center py-4">
                <div className="relative">
                  <div className="connection-line w-0.5 h-20 bg-gradient-to-b from-cyan-500/50 via-purple-500/50 to-orange-500/50 shadow-lg shadow-purple-500/20" />
                  <div className="particle absolute left-1/2 -translate-x-1/2 top-0 w-2 h-2 rounded-full bg-purple-400 blur-sm" />
                  <div className="particle absolute left-1/2 -translate-x-1/2 top-0 w-2 h-2 rounded-full bg-cyan-400 blur-sm" />
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-xs text-purple-400/80 whitespace-nowrap font-medium">
                    Kevlar Tether
                  </div>
                </div>
              </div>

              {/* Internal Module */}
              <div className="module-card bg-gradient-to-br from-orange-900/40 via-amber-900/30 to-slate-900/40 backdrop-blur-sm rounded-xl p-6 border border-orange-500/30 shadow-lg shadow-orange-500/20">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-orange-500/20 to-amber-500/20 border border-orange-400/40 flex items-center justify-center text-xs font-bold text-orange-300 shadow-inner shadow-orange-500/20">
                    INT
                  </div>
                  <div>
                    <div className="text-base font-semibold text-orange-100">
                      Internal Module
                    </div>
                    <div className="text-xs text-orange-400/70 mt-0.5">
                      Ingestible Sensor
                    </div>
                  </div>
                </div>
                <ul className="space-y-2 list-none text-sm text-slate-300">
                  <li className="pl-4 border-l-2 border-orange-500/40 py-1">
                    ISFET pH Sensor{" "}
                    <span className="text-xs px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 font-medium ml-2 border border-orange-400/30">
                      CONFIRMATION
                    </span>
                  </li>
                  <li className="pl-4 border-l-2 border-orange-500/40 py-1">
                    Biocompatible PEEK Casing
                  </li>
                  <li className="pl-4 border-l-2 border-orange-500/40 py-1">
                    Tethered Power & Data Link
                  </li>
                  <li className="pl-4 border-l-2 border-orange-500/40 py-1">
                    Acid-Resistant Design
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <DataFlow />
          {/* Section 2: Data Flow Logic */}

          {/* Section 3: Data Transmission */}
          <div className="bg-slate-900/40 backdrop-blur-xl rounded-2xl p-8 border border-blue-800/30 shadow-2xl shadow-blue-900/10">
            <h2 className="text-2xl font-semibold text-blue-300 mb-8 tracking-wide">
              3. Data Transmission Architecture
            </h2>
            <div className="grid gap-6">
              {[
                {
                  num: "1",
                  title: "Underwater Processing",
                  color: "blue",
                  items: [
                    {
                      label: "Trigger Detection:",
                      desc: "IMU monitors 24/7 in low-power mode",
                    },
                    {
                      label: "Confirmation:",
                      desc: "pH sensor activated only when needed",
                    },
                    {
                      label: "Feature Extraction:",
                      desc: "Hours of data → 3 key numbers",
                    },
                    {
                      label: "Compression:",
                      desc: "Complete predation event → <32 bytes",
                    },
                    {
                      label: "Prioritization:",
                      desc: "Confirmed kills get highest priority",
                    },
                  ],
                },
                {
                  num: "2",
                  title: "Surface Transmission",
                  color: "cyan",
                  items: [
                    {
                      label: "Surface Detection:",
                      desc: "Saltwater switch activates GPS/modem",
                    },
                    {
                      label: "Rapid GPS Fix:",
                      desc: "Fastloc acquires position in seconds",
                    },
                    {
                      label: "Priority Burst:",
                      desc: "High-value data transmitted first",
                    },
                    {
                      label: "Multiple Attempts:",
                      desc: "Repeated bursts maximize success",
                    },
                    {
                      label: "Power Management:",
                      desc: "Quick on/off to conserve battery",
                    },
                  ],
                },
                {
                  num: "3",
                  title: "Satellite Relay",
                  color: "indigo",
                  items: [
                    {
                      label: "LEO Constellation:",
                      desc: "Argos satellites in Low Earth Orbit",
                    },
                    {
                      label: "Radio Reception:",
                      desc: "401.65 MHz signal capture",
                    },
                    {
                      label: "Doppler Processing:",
                      desc: "Signal analysis for backup location",
                    },
                    {
                      label: "Global Coverage:",
                      desc: "Polar-orbiting satellites worldwide",
                    },
                    {
                      label: "Ground Relay:",
                      desc: "Downlink to nearest receiving station",
                    },
                  ],
                },
                {
                  num: "4",
                  title: "Ground & User Access",
                  color: "violet",
                  items: [
                    {
                      label: "Data Processing:",
                      desc: "CLS decodes and validates packets",
                    },
                    {
                      label: "Quality Control:",
                      desc: "Error checking and data validation",
                    },
                    {
                      label: "Database Storage:",
                      desc: "Processed data archived securely",
                    },
                    {
                      label: "Web Portal:",
                      desc: "Scientists access via secure interface",
                    },
                    {
                      label: "API Access:",
                      desc: "Automated data integration for models",
                    },
                  ],
                  footer:
                    "[2025-09-27T14:03:00Z, -23.45°, 151.23°, CONFIRMED_KILL, pH=4.8, 5.5hrs]",
                },
              ].map((stage) => (
                <div
                  key={stage.num}
                  className={`bg-gradient-to-br from-${stage.color}-900/30 to-slate-900/50 backdrop-blur-sm rounded-xl p-6 border border-${stage.color}-500/30 flex gap-5 shadow-lg shadow-${stage.color}-500/10`}
                >
                  <div
                    className={`stage-number w-12 h-12 rounded-lg bg-gradient-to-br from-${stage.color}-500/30 to-${stage.color}-600/20 border border-${stage.color}-400/40 flex items-center justify-center text-lg font-bold text-${stage.color}-200 shrink-0 shadow-inner`}
                  >
                    {stage.num}
                  </div>
                  <div className="flex-1">
                    <div
                      className={`text-base font-semibold text-${stage.color}-100 mb-4`}
                    >
                      {stage.title}
                    </div>
                    <ul className="space-y-2.5 text-sm text-slate-300 leading-relaxed">
                      {stage.items.map((item, idx) => (
                        <li key={idx}>
                          <span
                            className={`font-medium text-${stage.color}-200`}
                          >
                            {item.label}
                          </span>{" "}
                          {item.desc}
                        </li>
                      ))}
                    </ul>
                    {stage.footer && (
                      <div
                        className="data-packet mt-4 bg-gradient-to-r from-violet-900/60 via-fuchsia-800/60 to-violet-900/60 border-2 border-violet-500/50 rounded-lg p-3 font-mono text-xs text-violet-200 shadow-lg shadow-violet-500/20"
                        style={{
                          backgroundSize: "200% 100%",
                          backgroundPosition: "0% center",
                        }}
                      >
                        {stage.footer}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
