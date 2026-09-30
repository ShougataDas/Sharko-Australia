import React, { useRef, forwardRef, useImperativeHandle } from "react";
import gsap from "gsap-trial";
import { ScrollTrigger } from "gsap-trial/ScrollTrigger";
// import { DrawSVGPlugin } from "gsap-trial/DrawSVGPlugin"; // Removed for production
import { MotionPathPlugin } from "gsap-trial/MotionPathPlugin";
import { useGSAP } from "@gsap/react";
import Img1 from "../assets/imu.png";
import Img2 from "../assets/amu.png";
import Img3 from "../assets/ph.png";
import Img4 from "../assets/4.png";
import Img5 from "../assets/feature.png";
import Img6 from "../assets/data.png";
const cmsData = [
  {
    title: "Low-Power Listening",
    content: "IMU continuously monitors for predatory signature",
    icon: Img1,
    color: "from-violet-900/30 to-slate-900/50 border-violet-500/30",
    footer: "Waiting for high-G lunge + violent shake pattern",
    footerColor: "text-violet-400/80",
  },
  {
    title: "TRIGGER DETECTED?",
    content: "Lunge + Shake Signature Found?",
    icon: Img2,
    color: "from-blue-900/30 to-slate-900/50 border-blue-500/30",
    footer: "",
    footerColor: "",
  },
  {
    title: "Active Confirmation",
    content: "Monitor internal pH sensor for 5-10 minutes",
    icon: Img3,
    color: "from-indigo-900/30 to-slate-900/50 border-indigo-500/30",
    footer: "Looking for pH spike (1.5 → 4.0+)",
    footerColor: "text-indigo-400/80",
  },
  {
    title: "CONFIRMATION DETECTED?",
    content: "pH Spike Within Time Window?",
    icon: Img4,
    color: "from-red-900/30 to-slate-900/50 border-red-500/30",
    footer: "",
    footerColor: "",
  },
  {
    title: "Feature Extraction",
    content: "Monitor complete digestion curve (hours)",
    icon: Img5,
    color: "from-green-900/30 to-slate-900/50 border-green-500/30",
    footerColor: "text-green-400/80",
    footer: "Extract: Peak pH, Duration, Timestamp",
  },
  {
    title: "Data Processing",
    content: "Compress to <32 bytes, queue for transmission",
    icon: Img6,
    color: "from-yellow-900/30 to-slate-900/50 border-yellow-500/30",
    footer:
      "[Timestamp, GPS, Event: Confirmed_Kill, pH_Peak: 4.8, Duration: 5.5hrs]",
    footerColor: "text-yellow-400/80",
  },
];

gsap.registerPlugin(useGSAP, ScrollTrigger, MotionPathPlugin);

// Removed DrawSVGPlugin for production deployment

type AnimationOptions = {
  drawFrom: number;
  contentOffset: number;
  start: string;
  end?: string;
  pulseAt?: "start" | "mid" | "end" | number;
};

function animateSection(
  refs: LineRefs | null,
  contentEl: Element | null,
  options: AnimationOptions,
  iconEl?: Element | null
) {
  const line = refs?.lineRef.current ?? null;
  const circle = refs?.circleRef.current ?? null;
  const pulse = refs?.pulseRef.current ?? null;

  if (!line || !circle || !pulse || !contentEl) {
    return gsap.timeline();
  }

  const l = line as SVGPathElement;
  const c = circle as SVGCircleElement;
  const p = pulse as SVGCircleElement;

  // Compute text reveal position and sync the big circle pulse to it
  const textStart = Math.max(0, (options.contentOffset ?? 0) - 0.9);

  return (
    gsap
      .timeline({
        defaults: { ease: "power1.out" },
        scrollTrigger: {
          trigger: line,
          scrub: true,
          start: options.start,
          end: options.end ?? "bottom center",
        },
      })
      .to(c, { autoAlpha: 1, duration: 0.05 })
      // Pop the big circle exactly when the small circle reaches the end point
      .to(
        p,
        {
          scale: 2,
          autoAlpha: 1,
          transformOrigin: "center",
          ease: "elastic(2.5, 1)",
        },
        textStart
      )
      .to(
        c,
        {
          // Cast to SVGPathElement for GSAP MotionPath types
          motionPath: {
            path: l,
            align: l,
            alignOrigin: [0.5, 0.5],
          },
          duration: 4,
          onUpdate: function () {
            // Calculate progress and update stroke dash offset to follow circle
            const progress = this.progress();
            const pathLength = l.getTotalLength();

            // Set stroke dash array to path length and offset to hide the part after circle
            gsap.set(l, {
              strokeDasharray: pathLength,
              strokeDashoffset: pathLength * (1 - progress),
            });
          },
        },
        0
      )
      // Eyecatching text + card reveal: masked wipe + blur fade + slight overshoot
      .set(contentEl, { overflow: "hidden" }, 0)
      .set(
        (contentEl as HTMLElement).closest(".content-card") as Element,
        { overflow: "hidden" },
        0
      )
      .fromTo(
        (contentEl as HTMLElement).closest(".content-card") as Element,
        { clipPath: "inset(0 100% 0 0)", opacity: 0.6 },
        {
          clipPath: "inset(0 0% 0 0)",
          opacity: 1,
          duration: 0.8,
          ease: "power3.out",
        },
        textStart
      )
      .fromTo(
        contentEl,
        { clipPath: "inset(0 100% 0 0)" },
        { clipPath: "inset(0 0% 0 0)", duration: 0.8, ease: "power3.out" },
        textStart
      )
      .from(
        [
          (contentEl as HTMLElement).querySelector("h2"),
          (contentEl as HTMLElement).querySelector("p"),
        ],
        {
          opacity: 0,
          y: 14,
          filter: "blur(6px)",
          duration: 0.8,
          ease: "power3.out",
          stagger: 0.08,
        },
        textStart + 0.02
      )
      // Bubble/jump effect for the card wrapper
      .from(
        (contentEl as HTMLElement).closest(".content-card") as Element,
        {
          scale: 0.96,
          y: 10,
          duration: 0.5,
          ease: "back.out(2)",
        },
        textStart
      )
      // Sheen sweep across the glass card
      .fromTo(
        (
          (contentEl as HTMLElement).closest(".content-card") as HTMLElement
        )?.querySelector(".card-sheen") as Element,
        { x: "-120%", opacity: 0 },
        { x: "140%", opacity: 1, duration: 0.9, ease: "power2.out" },
        textStart + 0.05
      )
      .from(
        (contentEl as HTMLElement).querySelector("h2"),
        {
          scale: 0.98,
          transformOrigin: "left center",
          duration: 0.3,
          ease: "back.out(2)",
        },
        textStart
      )
      .from(
        iconEl as Element,
        { opacity: 0, y: 8, duration: 0.6, ease: "power2.out" },
        textStart
      )
      .to(c, { autoAlpha: 0, duration: 0.0 }, 4)
  );
}

type LineRefs = {
  lineRef: React.RefObject<SVGPathElement>;
  circleRef: React.RefObject<SVGCircleElement>;
  pulseRef: React.RefObject<SVGCircleElement>;
};

const TopLine = forwardRef<LineRefs, object>((_, ref) => {
  const lineRef = useRef<SVGPathElement | null>(null);
  const circleRef = useRef<SVGCircleElement | null>(null);
  const pulseRef = useRef<SVGCircleElement | null>(null);

  useImperativeHandle(ref, () => ({
    lineRef: lineRef,
    circleRef: circleRef,
    pulseRef: pulseRef,
  }));

  return (
    <svg
      viewBox="0 0 48 92"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      className="block"
    >
      <defs>
        <linearGradient id="neonStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="50%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path
        ref={lineRef}
        stroke="url(#neonStroke)"
        filter="url(#glow)"
        d="M23 44C23 44 47.0237 62.7909 45.5 92"
        strokeWidth="2"
        fill="none"
      />
      <circle
        ref={circleRef}
        style={{ visibility: "hidden" }}
        className="invisible"
        r="2"
        cx="10"
        cy="10"
        fill="#8B5CF6"
      ></circle>
      <circle
        ref={pulseRef}
        style={{ visibility: "hidden" }}
        className="invisible"
        r="2.5"
        cx="23"
        cy="44"
        fill="#22D3EE"
      ></circle>
    </svg>
  );
});

const MiddleLine1 = forwardRef<LineRefs, object>((_, ref) => {
  const lineRef = useRef<SVGPathElement | null>(null);
  const circleRef = useRef<SVGCircleElement | null>(null);
  const pulseRef = useRef<SVGCircleElement | null>(null);
  useImperativeHandle(
    ref,
    () => {
      return {
        lineRef: lineRef,
        circleRef: circleRef,
        pulseRef: pulseRef,
      };
    },
    []
  );
  return (
    <svg
      viewBox="0 0 48 92"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      className="block"
    >
      <defs>
        <linearGradient id="neonStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="50%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path
        ref={lineRef}
        stroke="url(#neonStroke)"
        filter="url(#glow)"
        d="M45.5 0C45.059 12.6997 39.1134 27.3097 23.4444 42.9787C5.78037 60.6427 0.473512 77.0833 2.5 92"
        strokeWidth="2"
        fill="none"
      />
      <circle
        ref={circleRef}
        className="fill-purple-800 invisible"
        style={{ visibility: "hidden" }}
        r="2"
        cx="10"
        cy="10"
        fill="#8B5CF6"
      ></circle>
      <circle
        ref={pulseRef}
        style={{ visibility: "hidden" }}
        className="fill-purple-500 invisible"
        r="2.5"
        cx="20.5"
        cy="46"
        fill="#22D3EE"
      ></circle>
    </svg>
  );
});

const MiddleLine2 = forwardRef<LineRefs, object>((_, ref) => {
  const lineRef = useRef<SVGPathElement | null>(null);
  const circleRef = useRef<SVGCircleElement | null>(null);
  const pulseRef = useRef<SVGCircleElement | null>(null);

  useImperativeHandle(ref, () => ({
    lineRef: lineRef,
    circleRef: circleRef,
    pulseRef: pulseRef,
  }));

  return (
    <svg
      viewBox="0 0 48 92"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      className="block"
    >
      <defs>
        <linearGradient id="neonStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="50%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path
        ref={lineRef}
        stroke="url(#neonStroke)"
        filter="url(#glow)"
        d="M2.5 0C3.24752 12.7291 7.19307 27.3391 22.8621 43.0081C40.5261 60.6722 45.833 77.1127 45.5 92"
        strokeWidth="2"
        fill="none"
      />
      <circle
        ref={circleRef}
        className="ball ball01 fill-purple-800 invisible"
        style={{ visibility: "hidden" }}
        r="2"
        cx="10"
        cy="10"
        fill="#8B5CF6"
      ></circle>
      <circle
        ref={pulseRef}
        style={{ visibility: "hidden" }}
        className="fill-purple-500 invisible"
        r="2.5"
        cx="25.5"
        cy="46"
        fill="#22D3EE"
      ></circle>
    </svg>
  );
});

const BottomLine = forwardRef<LineRefs, object>((_, ref) => {
  const lineRef = useRef<SVGPathElement | null>(null);
  const circleRef = useRef<SVGCircleElement | null>(null);
  const pulseRef = useRef<SVGCircleElement | null>(null);

  useImperativeHandle(ref, () => ({
    lineRef: lineRef,
    circleRef: circleRef,
    pulseRef: pulseRef,
  }));
  return (
    <svg
      viewBox="0 0 48 92"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      className="block"
    >
      <defs>
        <linearGradient id="neonStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="50%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path
        ref={lineRef}
        stroke="url(#neonStroke)"
        filter="url(#glow)"
        d="M45.5 0C45.5087 27.0272 23 45.0788 23 45.0788"
        strokeWidth="2"
        fill="none"
      />
      <circle
        ref={circleRef}
        className="fill-purple-800 invisible"
        style={{ visibility: "hidden" }}
        r="2"
        cx="10"
        cy="10"
        fill="#8B5CF6"
      ></circle>
      <circle
        ref={pulseRef}
        style={{ visibility: "hidden" }}
        className="fill-purple-500 invisible"
        r="2.5"
        cx="23"
        cy="44"
        fill="#22D3EE"
      ></circle>
    </svg>
  );
});

type IndexProps = { index: number };

const TopContent = ({ index }: IndexProps) => {
  const topRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<LineRefs | null>(null);
  useGSAP(
    () => {
      const contentText = document.querySelector(
        `.content-text[data-index="${index}"]`
      );
      const contentIcon = document.querySelector(
        `.content-icon[data-index="${index}"]`
      );
      animateSection(
        svgRef.current,
        contentText,
        {
          drawFrom: 0,
          contentOffset: 0,
          start: "top center",
          pulseAt: "end",
        },
        contentIcon
      );
    },
    { scope: topRef, dependencies: [index] }
  );
  return (
    <div
      ref={topRef}
      className="h-[320px] sm:h-[420px] md:h-[520px] w-full      items-center m-0"
    >
      <TopLine ref={svgRef} />
    </div>
  );
};

const MiddleContentOne = ({ index }: IndexProps) => {
  const middleOneRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<LineRefs | null>(null);
  useGSAP(
    () => {
      const contentText = document.querySelector(
        `.content-text[data-index="${index}"]`
      );
      const contentIcon = document.querySelector(
        `.content-icon[data-index="${index}"]`
      );
      animateSection(
        svgRef.current,
        contentText,
        {
          drawFrom: -1,
          contentOffset: 2.07,
          start: "top center",
          pulseAt: "end",
        },
        contentIcon
      );
    },
    { scope: middleOneRef, dependencies: [index] }
  );
  return (
    <div
      ref={middleOneRef}
      className="h-[320px] sm:h-[420px] md:h-[520px] w-full items-center m-0"
    >
      <MiddleLine1 ref={svgRef} />
    </div>
  );
};

const MiddleContentTwo = ({ index }: IndexProps) => {
  const middleTwoRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<LineRefs | null>(null);
  useGSAP(
    () => {
      const contentText = document.querySelector(
        `.content-text[data-index="${index}"]`
      );
      const contentIcon = document.querySelector(
        `.content-icon[data-index="${index}"]`
      );
      animateSection(
        svgRef.current,
        contentText,
        {
          drawFrom: 0,
          contentOffset: 2.07,
          start: "top center",
          pulseAt: "mid",
        },
        contentIcon
      );
    },
    { scope: middleTwoRef, dependencies: [index] }
  );
  return (
    <div
      ref={middleTwoRef}
      className="h-[320px] sm:h-[420px] md:h-[520px] w-full items-center m-0"
    >
      <MiddleLine2 ref={svgRef} />
    </div>
  );
};

const BottomContent = ({ index }: IndexProps) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<LineRefs | null>(null);
  useGSAP(
    () => {
      const contentText = document.querySelector(
        `.content-text[data-index="${index}"]`
      );
      const contentIcon = document.querySelector(
        `.content-icon[data-index="${index}"]`
      );
      animateSection(
        svgRef.current,
        contentText,
        {
          drawFrom: 0,
          contentOffset: 4,
          start: "top center",
          end: "bottom center",
          pulseAt: "mid",
        },
        contentIcon
      );
    },
    { scope: bottomRef, dependencies: [index] }
  );
  return (
    <div
      ref={bottomRef}
      className="h-[320px] sm:h-[420px] md:h-[520px] w-full items-center m-0"
    >
      <BottomLine ref={svgRef} />
    </div>
  );
};

function DataFlow() {
  return (
    <>
      <div id="wrapper" className="flex flex-col text-slate-100 bg-transparent">
        <h2 className="absolute top-[50px] left-0 text-2xl font-semibold text-purple-300 tracking-wide ">
          2. AI Data Flow & Decision Logic
        </h2>
        {cmsData.map((d, index) => {
          const first = index === 0;
          const last = index === cmsData.length - 1;
          const showMiddleLine1 = !first && !last && index % 2 !== 0;

          const line = first ? (
            <TopContent index={index} />
          ) : last ? (
            <BottomContent index={index} />
          ) : showMiddleLine1 ? (
            <MiddleContentOne index={index} />
          ) : (
            <MiddleContentTwo index={index} />
          );

          return (
            <div key={index} className="flex items-center justify-center py-0">
              <div className="shrink-0 content-icon" data-index={index}>
                <img
                  src={d.icon}
                  alt={d.title}
                  className="w-[200px] h-[200px]"
                />
              </div>
              <div className="h-auto w-[45%]">{line}</div>
              <div
                className={`content-card min-w-[450px] relative overflow-hidden bg-gradient-to-br ${d.color} rounded-xl p-5 border backdrop-blur-md`}
              >
                <div className="card-sheen pointer-events-none absolute inset-y-0 -left-full w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent blur-md none"></div>
                <div
                  className="flex flex-col content-text max-w-prose"
                  data-index={index}
                >
                  <h2 className="text-2xl font-bold mb-1">{d.title}</h2>
                  <p className="text-slate-300 leading-relaxed">{d.content}</p>
                  <br />
                  <span className={`${d.footerColor} text-xs`}>{d.footer}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

export default DataFlow;
