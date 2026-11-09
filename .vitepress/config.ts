import { defineConfig } from "vitepress";
import llms from "vitepress-plugin-llms";

export default defineConfig({
  title: "9aia workspace",
  description:
    "The 9aia org metarepo — every repo of the org cloned under repos/, managed by lasius.",
  base: "/workspace/",
  head: [["link", { rel: "icon", href: "/workspace/favicon.svg" }]],
  themeConfig: {
    nav: [
      { text: "Guide", link: "/" },
      { text: "lasius", link: "https://9aia.com/lasius/" },
      { text: "GitHub", link: "https://github.com/9aia/workspace" },
    ],
    sidebar: [
      {
        text: "Start",
        items: [{ text: "Introduction", link: "/" }],
      },
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/9aia/workspace" }],
  },
  plugins: [llms()],
});
