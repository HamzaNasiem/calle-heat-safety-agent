export interface LetsScrollSection {
  id: string
  label: string
  still?: string
  stillMobile?: string
  clip?: string
  clipMobile?: string
  accent?: string
  scroll?: number
  linger?: number
  eyebrow?: string
  title?: string
  body?: string
  tags?: string[]
  cta?: {
    primary?: { label: string; href: string }
    secondary?: { label: string; href: string }
  }
}

export interface LetsScrollConfig {
  brand?: { name: string; href?: string }
  diveScroll?: number
  connScroll?: number
  crossfade?: number
  hint?: string
  nav?: boolean
  atmosphere?: boolean
  sections: LetsScrollSection[]
  connectors?: string[]
  connectorsMobile?: string[]
  cta?: { label: string; href: string }
}

export function mountLetsScroll(container: HTMLElement, config: LetsScrollConfig): void
