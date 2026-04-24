/**
 * SafeMarkdown — the one ReactMarkdown wrapper the app uses.
 *
 * Bakes in:
 *   - remark-gfm for tables / strikethrough / task lists
 *   - rehype-sanitize with the default schema, which drops
 *     <script>, onerror= attributes, javascript: URLs, iframes, etc.
 *
 * LLM-produced markdown and workspace-authored docs are both rendered
 * through this component. Please do NOT import ReactMarkdown directly
 * in the rest of the app — an XSS regression is easy to miss in review
 * and this gives us a single place to evolve the sanitize policy.
 */
import type { ComponentProps } from "react";
import ReactMarkdown from "react-markdown";
import type { PluggableList } from "unified";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";

type ReactMarkdownProps = ComponentProps<typeof ReactMarkdown>;

export type SafeMarkdownProps = Omit<
  ReactMarkdownProps,
  "remarkPlugins" | "rehypePlugins"
> & {
  /** Additional remark plugins appended after remark-gfm. */
  remarkPlugins?: PluggableList;
  /** Additional rehype plugins appended after rehype-sanitize. */
  rehypePlugins?: PluggableList;
};

export function SafeMarkdown({
  remarkPlugins,
  rehypePlugins,
  ...rest
}: SafeMarkdownProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, ...(remarkPlugins ?? [])]}
      rehypePlugins={[rehypeSanitize, ...(rehypePlugins ?? [])]}
      {...rest}
    />
  );
}

export default SafeMarkdown;
