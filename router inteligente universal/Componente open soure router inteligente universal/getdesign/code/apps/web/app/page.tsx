import { HomePage } from "./_components/home/home-page";
import { JsonLd } from "./_components/json-ld";
import { MarketingShell } from "./_components/marketing-shell";
import { SiteFooter } from "./_components/site-footer";
import { SITE_DOMAIN } from "./_lib/site";
import { HOME_FAQ } from "./_lib/faq";

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: HOME_FAQ.map(({ question, answer }) => ({
    "@type": "Question",
    name: question,
    acceptedAnswer: { "@type": "Answer", text: answer },
  })),
};

const breadcrumbJsonLd = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    {
      "@type": "ListItem",
      position: 1,
      name: "Home",
      item: SITE_DOMAIN,
    },
  ],
};

export default function Home() {
  return (
    <MarketingShell footer={<SiteFooter />}>
      <HomePage />
      <JsonLd data={[faqJsonLd, breadcrumbJsonLd]} />
    </MarketingShell>
  );
}
