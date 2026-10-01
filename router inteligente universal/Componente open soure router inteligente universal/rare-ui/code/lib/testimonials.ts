export type Testimonial = {
  handle: string;
  quote: string;
  name?: string;
  href?: string;
  role?: string;
};

export function avatarUrl(handle: string) {
  return `https://unavatar.io/x/${handle.replace("@", "")}`;
}

export const TESTIMONIALS: Testimonial[] = [
  {
    name: "Pranav Mailarpawar",
    handle: "@pranvtwt",
    role: "Founder at ihatepdf.cv",
    quote: "Gonna use it in the next project",
    href: "https://x.com/pranvtwt/status/2089743483078856971",
  },
  {
    name: "Toolfolio",
    handle: "@toolfolio",
    role: "Founder",
    quote: "Niche library of Animated React Components",
    href: "https://x.com/toolfolio/status/2089745439624974755",
  },
  {
    name: "こぎそ",
    handle: "@kgsi",
    quote: "Rare UI: unique React components using Motion",
    href: "https://x.com/kgsi/status/2092472250708693049",
  },
  {
    name: "Kartik",
    handle: "@code_kartik",
    role: "MTS at Mem0",
    quote:
      "i used a few components from RareUI and took inspiration from other portfolio sites. overall, the results turned out pretty good.",
    href: "https://x.com/code_kartik/status/2096300833583624261",
  },
  {
    name: "Putri Karunia",
    handle: "@putrikarunian",
    role: "Founder at Lunagraph",
    quote: "excited to see rareui on it!",
    href: "https://x.com/putrikarunian/status/2094822945222963244",
  },
  {
    name: "Sergio",
    handle: "@LgyLight",
    quote:
      "每一个组件都很精致且独特，用 shadcn CLI 一行命令就能装，做产品真的离不开这些好东西，省事又好看，比让 AI 发挥稳定多了",
    href: "https://x.com/LgyLight/status/2096853942936498498",
  },
  {
    name: "Ali Bey",
    handle: "@alibey_10",
    role: "Founder at shoogle.dev",
    quote: "if you like Skiper UI, you're gonna love these too",
    href: "https://x.com/alibey_10/status/2089637255438586230",
  },
  {
    name: "Saman Pandey",
    handle: "@WarBornePhoenix",
    quote:
      "used some components in my flagship project Dreamer.. rareui is really sick!!",
    href: "https://x.com/WarBornePhoenix/status/2089809832794873858",
  },
  {
    name: "Tarunya Kesh",
    handle: "@TarunyaKesh",
    quote: "Using it for my designs, fs !!",
    href: "https://x.com/TarunyaKesh/status/2090133782032760881",
  },
  {
    name: "扉川川",
    handle: "@Feichuans",
    quote:
      "The meticulous design, interesting interaction and just-right animation effects, I love this",
    href: "https://x.com/Feichuans/status/2096768951435043195",
  },
  {
    name: "dev",
    handle: "@dsllwn",
    role: "Developer",
    quote:
      "dude i stumbled across it today for the orb component! awesome work!",
    href: "https://x.com/dsllwn/status/2096976552194138149",
  },
  {
    name: "Arnav Upadhyay",
    handle: "@Arnav_Upadhyay7",
    role: "Developer",
    quote: "All the components are super cool and well polished, crazy work",
    href: "https://x.com/Arnav_Upadhyay7/status/2096655302771065148",
  },
  {
    name: "Di Zhang",
    handle: "@di_zhang_fdu",
    role: "ex-NVIDIA, Alibaba",
    quote:
      "Rare UI is a great example of making polished interaction primitives easy to reuse",
    href: "https://x.com/di_zhang_fdu/status/2097049190186811635",
  },
  {
    name: "Abhishek",
    handle: "@Abhi_SDev",
    role: "Design engineer at Aave",
    quote:
      "Found out about RareUI and it has some crazy components for portfolio",
    href: "https://x.com/Abhi_SDev/status/2096333394984747134",
  },
  {
    name: "Aditya",
    handle: "@AdiKodez",
    role: "Developer",
    quote: "amazing , really like your rare ui project",
    href: "https://x.com/AdiKodez/status/2096981429783781780",
  },
  {
    name: "UXdesigner",
    handle: "@UXdesigner42869",
    role: "UX designer",
    quote: "The sidebar suddenly feels much more tactile",
    href: "https://x.com/UXdesigner42869/status/2094521622703087923",
  },
  {
    handle: "@cyze_dev",
    role: "Lead Product Engineer at Avatone",
    quote: "Word on the street is that rareui.com freakin' rad",
    href: "https://x.com/cyze_dev/status/2089787298762138074",
  },
  {
    handle: "@noechague",
    role: "Engineer at Bitstack",
    quote: "hey dude, what you're doing is really cool",
  },
  {
    handle: "@calcsam",
    role: "CEO and founder at Mastra",
    quote: "Your stuff is super cool",
  },
  {
    handle: "@siyabuilt",
    role: "Founder at roles.at",
    quote: "I just saw rareUI and I had to follow you, it's so beautiful",
  },
  {
    handle: "@pedrooladeira",
    role: "Engineer at dub.sh",
    quote: "I liked what you are building at rareui",
  },
  {
    handle: "@Rahulsainlll",
    role: "Founder at Keizer Works",
    quote:
      "Rareui is really good i am using this in one of our products right now",
  },
];
