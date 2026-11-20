export type BrandSystem = {
  id: string;
  displayFont: string;
  bodyFont: string;
  colors: { bg: string; ink: string; primary: string; accent: string; muted: string };
  radius: string;
  density: string;
};

export type CategoryProfile = {
  category: string;
  layoutFamily: string;
  defaultBrand: string;
  pages: string[];
  sections: string[];
  nav: { href: string; label: string }[];
};

export type LeadInput = {
  id: string;
  name: string;
  city?: string | null;
  region?: string | null;
  category?: string | null;
  contactPhone?: string | null;
  contactEmail?: string | null;
  fitReason?: string | null;
};

export type SiteComposition = {
  leadId: string;
  category: string;
  layoutFamily: string;
  brandSystemId: string;
  brand: BrandSystem;
  sections: string[];
  pages: string[];
  nav: { href: string; label: string }[];
  structuralSignature: string;
};
