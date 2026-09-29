"use client";
import React, { useState } from "react";
import { BookOpen, TrendingUp } from "lucide-react";
import { ComprehensiveResearchStudio } from "./ComprehensiveResearchStudio";
import { UnifiedResearchTradeFlow } from "./UnifiedResearchTradeFlow";

type TabType = "research" | "unified";

export function ResearchHub() {
  const [activeTab, setActiveTab] = useState<TabType>("research");

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Tab Navigation */}
      <div className="border-b border-border/40 bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-0">
          <div className="flex gap-8">
            {/* Research Tab */}
            <button
              onClick={() => setActiveTab("research")}
              className={`py-4 px-2 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
                activeTab === "research"
                  ? "border-blue-500 text-blue-500"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Research Studio
            </button>

            {/* Unified Flow Tab */}
            <button
              onClick={() => setActiveTab("unified")}
              className={`py-4 px-2 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
                activeTab === "unified"
                  ? "border-blue-500 text-blue-500"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Research-to-Trade Flow
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "research" && <ComprehensiveResearchStudio />}
        {activeTab === "unified" && <UnifiedResearchTradeFlow />}
      </div>
    </div>
  );
}
