import { redirect } from "next/navigation";

export default function SkillsIndexPage() {
  redirect("/skills/library");

  // This won't be rendered, but Next.js requires a component to be returned
  return null;
}
