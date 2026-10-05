"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X, BarChart2, FileSearch, MessageSquare, TrendingUp, Search, SlidersHorizontal, GraduationCap, Bell } from "lucide-react";
import { NavigationItem } from "@/components/glass";
import clsx from "clsx";

const mainNav = [
  { label: "Dashboard", icon: BarChart2, href: "/" },
  { label: "Market Overview", icon: BarChart2, href: "/market" },
  { label: "Research Studio", icon: FileSearch, href: "/research" },
  { label: "Ask PSX Pulse", icon: MessageSquare, href: "/research-ask", disabled: true },
  { label: "Trade Planning", icon: TrendingUp, href: "/research?tab=trade" },
  { label: "Company Search", icon: Search, href: "/search", disabled: true },
  { label: "Screeners", icon: SlidersHorizontal, href: "/screener" },
  { label: "Academy", icon: GraduationCap, href: "#", disabled: true },
  { label: "Watchlists & Alerts", icon: Bell, href: "#", disabled: true },
];

export default function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "#") return false;
    return href === "/" ? pathname === "/" : pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Menu Button - Top Right */}
      <button
        onClick={() => setOpen(!open)}
        className="lg:hidden fixed top-4 right-4 z-50 h-10 w-10 flex items-center justify-center rounded-lg bg-[#10161A] text-white shadow-md hover:shadow-lg transition-shadow"
        aria-label="Toggle menu"
        aria-expanded={open}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile Navigation Drawer */}
      {open && (
        <>
          {/* Backdrop */}
          <div
            className="lg:hidden fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div className="lg:hidden fixed top-0 left-0 right-0 z-40 max-h-screen overflow-y-auto bg-white/90 backdrop-blur-xl border-b border-[rgba(255,255,255,0.72)]">
            <div className="p-6 pt-20">
              {/* Logo */}
              <div className="mb-8 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#10161A] text-white shadow-md">
                  <BarChart2 size={18} />
                </div>
                <div className="flex flex-col">
                  <span className="text-base font-bold text-[#10161A]">
                    PSX<span className="text-[#566680] font-medium ml-1">Pulse</span>
                  </span>
                  <span className="text-[9px] uppercase font-semibold tracking-wider text-[#8E9CB7]">
                    Research
                  </span>
                </div>
              </div>

              {/* Navigation */}
              <p className="mb-4 px-3 text-[10px] font-semibold uppercase tracking-wider text-[#566680]">
                Menu
              </p>
              <nav className="flex flex-col gap-2">
                {mainNav.map(({ label, icon: Icon, href, disabled }) => (
                  <NavigationItem
                    key={label}
                    href={href}
                    label={label}
                    icon={<Icon size={16} />}
                    isActive={isActive(href)}
                    badge={disabled ? "soon" : undefined}
                    disabled={disabled}
                  />
                ))}
              </nav>
            </div>
          </div>
        </>
      )}
    </>
  );
}
