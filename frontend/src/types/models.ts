export interface ImageRef {
  id: string;
  src: string;
  alt: string;
}

export interface SectionOutput {
  id: string;
  title: string;
  summary?: string;
  analysis?: string;
  points?: string[];
  image?: ImageRef;
  rawJson?: any;
  dashboard?: string;
}

export interface AgentTab {
  id: string;
  label: string;
  sections: SectionOutput[];
}

export interface AgentView {
  id: string;
  name: string;
  tabs?: AgentTab[];
  sections?: SectionOutput[];
}

export interface WorkflowStage {
  id: string;
  name: string;
  status: 'completed' | 'in-progress' | 'pending';
  output?: string;
}

// Stock Analysis JSON structure
export interface StockSection {
  id: string;
  summary?: string;
  image?: string;
}

export interface StockAnalysisData {
  sections: StockSection[];
}

// Investment Analysis JSON structure
export interface InvestmentSection {
  id: string;
  analysis?: string;
  dashboard?: string;
}

export interface InvestmentAnalysisData {
  sections: InvestmentSection[];
  recommendation?: string;
  key_strengths?: string[];
  key_challenges?: string[];
}

// Compliance JSON structures
export interface ComplianceFinding {
  section_1_policy_rules?: string;
  section_2_trading_classification?: string;
  section_3_exceptional_events?: string;
}

export interface ComplianceRecommendation {
  section_4_final_recommendation?: string;
}
