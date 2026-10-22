/*
 * A link into the reader's own Heimdall dashboard, for a page that says "open X in the
 * dashboard". The dashboard asks which server to open (skipped when they have one), signs
 * them in first if needed, and lands on that page.
 *
 *   import { DashboardLink } from "/snippets/dashboard-link.jsx";
 *   Open <DashboardLink to="tickets/categories">**Tickets > Categories**</DashboardLink>.
 *
 * `to` is a key from Heimdall's docs/generated/dashboard-links.json, which CI checks every
 * use against, so a page cannot link to a dashboard page that no longer exists.
 *
 * The dashboard host is written here and nowhere else, so moving the dashboard is a one-line
 * change. It is inside the component because a snippet file's exports are the only thing a
 * page can import.
 */
export const DashboardLink = ({ to, children }) => {
  const dashboard = "https://bot.bifrost.gg";
  return (
    <a href={`${dashboard}/go/${to}`} target="_blank" rel="noopener">
      {children}
    </a>
  );
};
