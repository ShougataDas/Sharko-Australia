"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { X } from "lucide-react";

interface SensorDiagramProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SensorDiagram({ isOpen, onClose }: SensorDiagramProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!panelRef.current || !contentRef.current) return;

    if (isOpen) {
      // Reset initial states
      gsap.set([panelRef.current, contentRef.current], { clearProps: "all" });

      // Slide in animation with elastic effect
      gsap.fromTo(
        panelRef.current,
        { x: "-100%", opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 1.2,
          ease: "elastic.out(1, 0.3)",
        }
      );

      // Title animation with typewriter effect
      if (titleRef.current) {
        gsap.fromTo(
          titleRef.current,
          { opacity: 0, y: -30, scale: 0.8 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.8,
            delay: 0.3,
            ease: "back.out(1.7)",
          }
        );
      }

      // Stagger content animation with wave effect
      gsap.fromTo(
        contentRef.current.children,
        { opacity: 0, x: -80, rotationY: -15 },
        {
          opacity: 1,
          x: 0,
          rotationY: 0,
          duration: 0.8,
          stagger: {
            amount: 0.6,
            from: "start",
            ease: "power2.out",
          },
          delay: 0.6,
          ease: "power2.out",
        }
      );

      // Floating animation for close button
      gsap.to(".close-button", {
        y: -5,
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "power2.inOut",
        delay: 1.5,
      });

      // Subtle breathing animation for cards
      gsap.to(".glass-card", {
        scale: 1.02,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "power2.inOut",
        stagger: 0.2,
        delay: 2,
      });
    } else {
      // Slide out animation with scale effect
      gsap.to(panelRef.current, {
        x: "-100%",
        scale: 0.95,
        opacity: 0,
        duration: 0.5,
        ease: "power3.in",
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={panelRef}
      className="fixed left-0 top-0 h-screen w-1/2 z-[150] overflow-y-auto hide-scrollbar bg-slate-800/30 backdrop-blur-3xl border-r border-slate-600/20 shadow-2xl"
      style={{ transform: "translateX(-100%)" }}
    >
      {/* Glassmorphism Panel */}
      <div className="h-full relative">
        {/* Content Container */}
        <div className="relative z-10 h-full">
          {/* Close Button */}
          <div className="sticky top-0 z-20 flex justify-end p-6 ">
            <button
              onClick={onClose}
              className="close-button bg-slate-700/40 hover:bg-slate-600/50 backdrop-blur-sm border border-slate-500/30 rounded-full shadow-lg transition-all duration-300"
            >
              <X className="w-8 h-8 text-slate-200" />
            </button>
          </div>

          {/* Content */}
          <div ref={contentRef} className="px-8 pb-8 space-y-8">
            {/* Title */}
            <div ref={titleRef} className="text-center space-y-2  glass-card ">
              <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-300 to-slate-100 drop-shadow-lg">
                Smart Fusion Metabolic Kill Tag
              </h1>
              <p className="text-lg text-slate-400">
                System Architecture & Data Flow
              </p>
            </div>

            {/* Section 1: System Architecture */}
            <div className="glass-card">
              <h2 className="section-title text-slate-300">
                1. System Architecture
              </h2>
              <div className="space-y-6">
                {/* External Module */}
                <div className="module-card bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                  <div className="module-title">
                    🦈 EXTERNAL MODULE ("THE HUB")
                    <br />
                    <span className="text-sm font-normal text-slate-400">
                      Dorsal Fin Mount
                    </span>
                  </div>
                  <ul className="component-list">
                    <li>🔋 Main Battery (Li-ion)</li>
                    <li>🧠 Microcontroller (AI Processor)</li>
                    <li>📡 Fastloc-GPS & Argos Modem</li>
                    <li>
                      📊 IMU (9-axis: Accel, Gyro, Mag){" "}
                      <span className="highlight">TRIGGER</span>
                    </li>
                    <li>💾 Data Storage & Processing</li>
                  </ul>
                </div>

                {/* Tether */}
                <div className="flex items-center justify-center">
                  <div className="relative">
                    <div className="w-2 h-16 bg-gradient-to-b from-slate-500 to-slate-400 rounded-full shadow-lg shadow-slate-500/30" />
                    <div className="absolute left-8 top-1/2 -translate-y-1/2 text-sm text-slate-300 font-semibold whitespace-nowrap">
                      Kevlar Tether (Power & Data)
                    </div>
                  </div>
                </div>

                {/* Internal Module */}
                <div className="module-card bg-gradient-to-br from-slate-600/30 to-slate-700/30 border-slate-500/20">
                  <div className="module-title">
                    💊 INTERNAL MODULE ("THE PILL")
                    <br />
                    <span className="text-sm font-normal text-slate-400">
                      Ingestible Sensor
                    </span>
                  </div>
                  <ul className="component-list">
                    <li>
                      🧪 ISFET pH Sensor{" "}
                      <span className="highlight">CONFIRMATION</span>
                    </li>
                    <li>🛡️ Biocompatible PEEK Casing</li>
                    <li>🔗 Tethered Power & Data Link</li>
                    <li>⚡ Acid-Resistant Design</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Section 2: Data Flow Logic */}
            <div className="glass-card">
              <h2 className="section-title text-slate-300">
                2. AI Data Flow & Decision Logic
              </h2>
              <div className="space-y-4">
                <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                  <div className="font-bold text-slate-100 mb-2">
                    🔍 Stage 1: Low-Power Listening
                  </div>
                  <div className="text-sm text-slate-300">
                    IMU continuously monitors for predatory signature
                    <br />
                    <em className="text-slate-400">
                      Waiting for high-G lunge + violent shake pattern
                    </em>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-slate-400 drop-shadow-lg" />
                </div>

                <div className="decision-step">
                  <div className="font-bold text-slate-100 mb-2">
                    ❓ TRIGGER DETECTED?
                  </div>
                  <div className="text-sm text-slate-300">
                    Lunge + Shake Signature Found?
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flow-step bg-gradient-to-br from-slate-600/30 to-slate-700/30 border-slate-500/20">
                    <div className="font-bold text-slate-100 mb-2">❌ NO</div>
                    <div className="text-sm text-slate-300">
                      Continue Listening
                      <br />
                      <em className="text-slate-400">Stay in low-power mode</em>
                    </div>
                  </div>
                  <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                    <div className="font-bold text-slate-100 mb-2">✅ YES</div>
                    <div className="text-sm text-slate-300">
                      Activate pH Monitoring
                      <br />
                      <em className="text-slate-400">
                        Enter active confirmation mode
                      </em>
                    </div>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-slate-400 drop-shadow-lg" />
                </div>

                <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                  <div className="font-bold text-slate-100 mb-2">
                    🧪 Stage 2: Active Confirmation
                  </div>
                  <div className="text-sm text-slate-300">
                    Monitor internal pH sensor for 5-10 minutes
                    <br />
                    <em className="text-slate-400">
                      Looking for pH spike (1.5 → 4.0+)
                    </em>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-slate-400 drop-shadow-lg" />
                </div>

                <div className="decision-step">
                  <div className="font-bold text-slate-100 mb-2">
                    ❓ CONFIRMATION DETECTED?
                  </div>
                  <div className="text-sm text-slate-300">
                    pH Spike Within Time Window?
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flow-step bg-gradient-to-br from-slate-600/30 to-slate-700/30 border-slate-500/20">
                    <div className="font-bold text-slate-100 mb-2">❌ NO</div>
                    <div className="text-sm text-slate-300">
                      Log "Failed Attempt"
                      <br />
                      <em className="text-slate-400">
                        Return to listening mode
                      </em>
                    </div>
                  </div>
                  <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                    <div className="font-bold text-slate-100 mb-2">✅ YES</div>
                    <div className="text-sm text-slate-300">
                      CONFIRMED PREDATION!
                      <br />
                      <em className="text-slate-400">Begin full analysis</em>
                    </div>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-slate-400 drop-shadow-lg" />
                </div>

                <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                  <div className="font-bold text-slate-100 mb-2">
                    📊 Stage 3: Feature Extraction
                  </div>
                  <div className="text-sm text-slate-300">
                    Monitor complete digestion curve (hours)
                    <br />
                    Extract: Peak pH, Duration, Timestamp
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[20px] border-t-slate-400 drop-shadow-lg" />
                </div>

                <div className="flow-step bg-gradient-to-br from-slate-700/30 to-slate-600/30 border-slate-500/20">
                  <div className="font-bold text-slate-100 mb-2">
                    📤 Stage 4: Data Packet Creation
                  </div>
                  <div className="text-sm text-slate-300 mb-3">
                    Compress to &lt;32 bytes, queue for transmission
                  </div>
                  <div className="data-packet">
                    [Timestamp, GPS, Event: Confirmed_Kill, pH_Peak: 4.8,
                    Duration: 5.5hrs]
                  </div>
                </div>
              </div>
            </div>

            {/* Section 3: Data Transmission */}
            <div className="glass-card">
              <h2 className="section-title text-slate-300">
                3. Data Transmission Architecture
              </h2>
              <div className="grid gap-6">
                <div className="stage-card">
                  <div className="stage-title">
                    🏊‍♀️ Stage 1: Underwater Processing
                  </div>
                  <ul className="stage-list">
                    <li>
                      <span className="highlight">Trigger Detection:</span> IMU
                      monitors 24/7 in low-power mode
                    </li>
                    <li>
                      <span className="highlight">Confirmation:</span> pH sensor
                      activated only when needed
                    </li>
                    <li>
                      <span className="highlight">Feature Extraction:</span>{" "}
                      Hours of data → 3 key numbers
                    </li>
                    <li>
                      <span className="highlight">Compression:</span> Complete
                      predation event → &lt;32 bytes
                    </li>
                    <li>
                      <span className="highlight">Prioritization:</span>{" "}
                      Confirmed kills get highest priority
                    </li>
                  </ul>
                </div>

                <div className="stage-card">
                  <div className="stage-title">
                    🌊 Stage 2: Surface Transmission
                  </div>
                  <ul className="stage-list">
                    <li>
                      <span className="highlight">Surface Detection:</span>{" "}
                      Saltwater switch activates GPS/modem
                    </li>
                    <li>
                      <span className="highlight">Rapid GPS Fix:</span> Fastloc
                      acquires position in seconds
                    </li>
                    <li>
                      <span className="highlight">Priority Burst:</span>{" "}
                      High-value data transmitted first
                    </li>
                    <li>
                      <span className="highlight">Multiple Attempts:</span>{" "}
                      Repeated bursts maximize success
                    </li>
                    <li>
                      <span className="highlight">Power Management:</span> Quick
                      on/off to conserve battery
                    </li>
                  </ul>
                </div>

                <div className="stage-card">
                  <div className="stage-title">🛰️ Stage 3: Satellite Relay</div>
                  <ul className="stage-list">
                    <li>
                      <span className="highlight">LEO Constellation:</span>{" "}
                      Argos satellites in Low Earth Orbit
                    </li>
                    <li>
                      <span className="highlight">Radio Reception:</span> 401.65
                      MHz signal capture
                    </li>
                    <li>
                      <span className="highlight">Doppler Processing:</span>{" "}
                      Signal analysis for backup location
                    </li>
                    <li>
                      <span className="highlight">Global Coverage:</span>{" "}
                      Polar-orbiting satellites worldwide
                    </li>
                    <li>
                      <span className="highlight">Ground Relay:</span> Downlink
                      to nearest receiving station
                    </li>
                  </ul>
                </div>

                <div className="stage-card">
                  <div className="stage-title">
                    🖥️ Stage 4: Ground & User Access
                  </div>
                  <ul className="stage-list">
                    <li>
                      <span className="highlight">Data Processing:</span> CLS
                      decodes and validates packets
                    </li>
                    <li>
                      <span className="highlight">Quality Control:</span> Error
                      checking and data validation
                    </li>
                    <li>
                      <span className="highlight">Database Storage:</span>{" "}
                      Processed data archived securely
                    </li>
                    <li>
                      <span className="highlight">Web Portal:</span> Scientists
                      access via secure interface
                    </li>
                    <li>
                      <span className="highlight">API Access:</span> Automated
                      data integration for models
                    </li>
                  </ul>
                  <div className="data-packet mt-4">
                    Final Output: [2025-09-27T14:03:00Z, -23.45°, 151.23°,
                    CONFIRMED_KILL, pH=4.8, 5.5hrs]
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
