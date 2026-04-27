"""SVG Validation Agent - validates and fixes generated SVG animation code before presenting on UI."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

# SVG namespace; used for parsing and serialization.
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Namespace map for serialization (empty prefix = default)
NS_MAP = {None: SVG_NS, "xlink": XLINK_NS}


@dataclass
class SvgValidationResult:
    """Result of SVG validation: fixed SVG, errors detected, and fixes applied."""

    svg: str
    errors_found: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    parse_failed: bool = False


def _ns(tag: str, namespace: str = SVG_NS) -> str:
    """Return a namespaced tag for lookup."""
    if tag.startswith("{") or ":" in tag:
        return tag
    return f"{{{namespace}}}{tag}"


def _strip_ns(tag: str) -> str:
    """Return local name without namespace."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _fix_filter_femerge_mismatch(svg: str) -> str:
    """Fix 'Opening and ending tag mismatch: feMerge and filter' by ensuring
    every <feMerge> has a matching </feMerge> before </filter>.
    """
    if "</filter" not in svg and "<feMerge" not in svg:
        return svg
    out: list[str] = []
    i = 0
    while i < len(svg):
        open_filter = re.search(r"<filter\b", svg[i:], re.IGNORECASE)
        if not open_filter:
            out.append(svg[i:])
            break
        start = i + open_filter.start()
        out.append(svg[i:start])
        # j = after the opening <filter ...> tag (not just after "<filter")
        tag_end = svg.index(">", start) + 1
        j = tag_end
        depth = 1
        while depth > 0 and j < len(svg):
            next_close = re.search(r"</filter\s*>", svg[j:], re.IGNORECASE)
            next_open = re.search(r"<filter\b", svg[j:], re.IGNORECASE)
            if not next_close:
                out.append(svg[start:])
                return "".join(out)
            pos_close = j + next_close.start()
            pos_open = j + next_open.start() if next_open else len(svg)
            if next_open and pos_open < pos_close:
                depth += 1
                j = svg.index(">", pos_open) + 1
                continue
            depth -= 1
            if depth == 0:
                block = svg[start:pos_close]
                closing = svg[pos_close : j + next_close.end()]
                # Count opening <feMerge...> (excluding self-closing <feMerge ... />)
                open_tags = len(re.findall(r"<feMerge\s*[^>]*>", block, re.IGNORECASE))
                self_closing = len(re.findall(r"<feMerge\s*[^>]*/\s*>", block, re.IGNORECASE))
                close_femerge = len(re.findall(r"</feMerge\s*>", block, re.IGNORECASE))
                need_close = (open_tags - self_closing) - close_femerge
                if need_close > 0:
                    out.append(block)
                    out.append("</feMerge>" * need_close)
                else:
                    out.append(block)
                out.append(closing)
                i = j + next_close.end()
                break
            j = pos_close + len(next_close.group(0))
        else:
            out.append(svg[start:])
            break
    return "".join(out)


def _fix_stray_femerge_close_inside_filter(svg: str) -> str:
    """Fix 'Opening and ending tag mismatch: filter and feMerge' when the closing tag
    is </feMerge> but the open tag was <filter> (i.e. replace stray </feMerge> with </filter>
    when the filter block contains no opening <feMerge>).
    """
    if "<filter" not in svg or "</feMerge" not in svg:
        return svg
    result: list[str] = []
    pos = 0
    while True:
        open_m = re.search(r"<filter\b[^>]*>", svg[pos:], re.IGNORECASE)
        if not open_m:
            result.append(svg[pos:])
            break
        start = pos + open_m.start()
        end_open = pos + open_m.end()
        result.append(svg[pos:start])
        block_start = end_open
        next_filter = re.search(r"</filter\s*>", svg[block_start:], re.IGNORECASE)
        next_femerge = re.search(r"</feMerge\s*>", svg[block_start:], re.IGNORECASE)
        if not next_filter and not next_femerge:
            result.append(svg[block_start:])
            break
        # If </feMerge> appears before </filter> and there's no <feMerge in between, it's stray
        if next_femerge and (not next_filter or next_femerge.start() < next_filter.start()):
            between = svg[block_start : block_start + next_femerge.start()]
            if not re.search(r"<feMerge[\s/>]", between, re.IGNORECASE):
                # Keep the opening <filter> tag, content up to </feMerge>, then close with </filter>
                result.append(svg[start:end_open])  # include <filter ...>
                result.append(svg[block_start : block_start + next_femerge.start()])
                result.append("</filter>")
                pos = block_start + next_femerge.end()
                continue
        if next_filter:
            result.append(svg[start:end_open])  # opening <filter ...>
            result.append(svg[block_start : block_start + next_filter.end()])
            pos = block_start + next_filter.end()
        else:
            result.append(svg[block_start:])
            break
    return "".join(result)


def _collapse_duplicate_xmlns_in_string(svg: str) -> str:
    """Ensure the opening <svg> tag has at most one xmlns attribute (keep first).
    Fixes 'Attribute xmlns redefined' errors from model output or serialization.
    """
    match = re.search(r"<svg\s+([^>]*)\s*>", svg, re.IGNORECASE | re.DOTALL)
    if not match:
        return svg
    rest = match.group(1)
    # Match xmlns="..." or xmlns='...'
    xmlns_pattern = re.compile(
        r'\s*xmlns\s*=\s*(?:"[^"]*"|\'[^\']*\')\s*',
        re.IGNORECASE,
    )
    if xmlns_pattern.search(rest) is None:
        return svg
    # Remove all xmlns occurrences and keep the first one
    parts = xmlns_pattern.split(rest, maxsplit=1)
    if len(parts) <= 1:
        return svg
    first_block = parts[0].strip()
    after_first = parts[1].strip()
    after_first = xmlns_pattern.sub(" ", after_first).strip()
    first_match = xmlns_pattern.search(rest)
    if not first_match:
        return svg
    single_xmlns = first_match.group(0).strip()
    new_rest = " ".join(filter(None, [first_block, single_xmlns, after_first]))
    new_open = f"<svg {new_rest}>"
    return svg[: match.start()] + new_open + svg[match.end() :]


def _normalize_bom_and_whitespace(svg: str) -> tuple[str, list[str], list[str]]:
    """Strip BOM, normalize line endings to \\n, strip outer whitespace. Returns (svg, errors, fixes)."""
    errors: list[str] = []
    fixes: list[str] = []
    if svg.startswith("\ufeff"):
        svg = svg[1:]
        fixes.append("Removed BOM (byte order mark)")
    if "\r\n" in svg or "\r" in svg:
        svg = svg.replace("\r\n", "\n").replace("\r", "\n")
        fixes.append("Normalized line endings to LF")
    svg = svg.strip()
    return svg, errors, fixes


def _remove_invalid_xml_chars(svg: str) -> tuple[str, list[str], list[str]]:
    """Remove or replace control characters invalid in XML 1.0 (except \\t, \\n, \\r)."""
    errors: list[str] = []
    fixes: list[str] = []
    invalid = []
    for i, c in enumerate(svg):
        code = ord(c)
        if code in (9, 10, 13):
            continue
        if code < 32 or (0x7F <= code <= 0x84) or (0x86 <= code <= 0x9F):
            invalid.append(i)
    if invalid:
        svg = "".join(c for i, c in enumerate(svg) if i not in invalid)
        errors.append("Invalid XML 1.0 control characters in content")
        fixes.append("Removed invalid control characters")
    return svg, errors, fixes


def _fix_unescaped_ampersands_in_attributes(svg: str) -> tuple[str, list[str], list[str]]:
    """Escape bare & in attribute values (e.g. attr=\"a & b\" -> attr=\"a &amp; b\")."""
    errors: list[str] = []
    fixes: list[str] = []
    did_fix = [False]  # mutable so nested function can set

    def replace_amp(m: re.Match) -> str:
        key, quote, value = m.group(1), m.group(2), m.group(3)
        if "&" not in value:
            return m.group(0)
        # Don't double-escape existing entities
        new_val = re.sub(r"&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)", "&amp;", value)
        if new_val != value:
            did_fix[0] = True
        return f'{key}={quote}{new_val}{quote}'

    svg_new = re.sub(
        r'(\b\w+)=(")([^"]*)\2',
        replace_amp,
        svg,
        flags=re.IGNORECASE,
    )
    svg_new = re.sub(
        r"(\b\w+)=(')([^']*)\2",
        replace_amp,
        svg_new,
        flags=re.IGNORECASE,
    )
    if did_fix[0]:
        errors.append("Unescaped '&' in attribute value (invalid XML)")
        fixes.append("Escaped unescaped ampersand in attribute")
    return svg_new, errors, fixes


def _fix_unescaped_ampersands_in_attributes_simple(svg: str) -> str:
    """Escape bare & in double-quoted attribute values (for use when not collecting report)."""
    def repl(m: re.Match) -> str:
        key, q, val = m.group(1), m.group(2), m.group(3)
        if "&" not in val:
            return m.group(0)
        val = re.sub(r"&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)", "&amp;", val)
        return f"{key}={q}{val}{q}"
    svg = re.sub(r'(\b\w+)=(")([^"]*)\2', repl, svg, flags=re.IGNORECASE)
    svg = re.sub(r"(\b\w+)=(')([^']*)\2", repl, svg, flags=re.IGNORECASE)
    return svg


def _fix_duplicate_attributes_in_opening_tags(svg: str) -> tuple[str, list[str], list[str]]:
    """Remove duplicate attributes in opening tags (keep first occurrence)."""
    fixes: list[str] = []
    errors: list[str] = []

    def dedupe_tag(m: re.Match) -> str:
        rest = m.group(1)  # content between <svg and >
        seen: set[str] = set()
        # Match attr="value" or attr='value'
        parts = re.findall(r'(\s*(\w+)\s*=\s*(?:"[^"]*"|\'[^\']*\'))', rest)
        kept = []
        for part, name in parts:
            key = name.lower()
            if key in seen:
                errors.append(f"Duplicate attribute '{name}' in <svg>")
                fixes.append(f"Removed duplicate attribute '{name}'")
                continue
            seen.add(key)
            kept.append(part)
        return "<svg " + "".join(kept).strip() + ">"

    # Only dedupe <svg ...> to avoid breaking complex content
    svg_new = re.sub(r"<svg\s+([^>]*)\s*>", dedupe_tag, svg, count=1, flags=re.IGNORECASE | re.DOTALL)
    return svg_new, errors, fixes


class SvgValidationAgent:
    """
    Validates and fixes generated SVG animation code so it is safe and
    well-formed before being presented on the UI Dashboard.
    """

    def validate_and_fix_with_report(self, svg: str) -> SvgValidationResult:
        """
        Validate the SVG string, detect syntax/format errors, apply fixes, and return
        a result with fixed SVG, errors found, and fixes applied.
        """
        if not (svg or "").strip():
            return SvgValidationResult(svg="")

        all_errors: list[str] = []
        all_fixes: list[str] = []

        svg = svg.strip()
        # Pre-parse normalizations and fixers (order matters)
        svg, errs, fixs = _normalize_bom_and_whitespace(svg)
        all_errors.extend(errs)
        all_fixes.extend(fixs)

        svg, errs, fixs = _remove_invalid_xml_chars(svg)
        all_errors.extend(errs)
        all_fixes.extend(fixs)

        # Extract single root <svg> when response is wrapped
        before = svg
        svg = self._extract_svg_root(svg)
        if svg != before:
            all_fixes.append("Extracted single <svg> root from wrapped content")

        # Duplicate xmlns and feMerge fixes (string-level)
        before = svg
        svg = _collapse_duplicate_xmlns_in_string(svg)
        if svg != before:
            all_errors.append("Duplicate xmlns attribute in <svg>")
            all_fixes.append("Collapsed duplicate xmlns to single attribute")

        before = svg
        svg = _fix_filter_femerge_mismatch(svg)
        svg = _fix_stray_femerge_close_inside_filter(svg)
        if svg != before:
            all_errors.append("Unclosed <feMerge> inside <filter> (tag mismatch)")
            all_fixes.append("Closed missing </feMerge> before </filter>")

        # Escape unescaped & in attributes
        svg, errs, fixs = _fix_unescaped_ampersands_in_attributes(svg)
        all_errors.extend(errs)
        all_fixes.extend(fixs)

        # Duplicate attributes on <svg>
        svg, errs, fixs = _fix_duplicate_attributes_in_opening_tags(svg)
        all_errors.extend(errs)
        all_fixes.extend(fixs)

        # Try XML parse and tree-level fixes
        try:
            root = ET.fromstring(svg)
        except ET.ParseError as e:
            all_errors.append(f"XML parse error: {e}")
            all_fixes.append("Applied minimal regex-based fixes (parse failed)")
            fixed = self._minimal_fix(svg)
            return SvgValidationResult(
                svg=fixed,
                errors_found=all_errors,
                fixes_applied=all_fixes,
                parse_failed=True,
            )

        fixed = self._validate_and_fix_tree(root)
        if fixed is None:
            all_errors.append("Tree validation/serialization failed")
            all_fixes.append("Applied minimal regex-based fixes")
            fixed = self._minimal_fix(svg)
            return SvgValidationResult(
                svg=fixed,
                errors_found=all_errors,
                fixes_applied=all_fixes,
                parse_failed=True,
            )

        # Tree fixes we apply (could be extended to report which were applied)
        all_fixes.append("Validated and fixed tree (root attributes, scripts/events removed)")
        return SvgValidationResult(
            svg=fixed,
            errors_found=all_errors,
            fixes_applied=all_fixes,
            parse_failed=False,
        )

    def validate_and_fix(self, svg: str) -> str:
        """
        Validate the SVG string and apply fixes. Returns the validated/fixed
        SVG, or the original string if parsing fails and no safe fix is possible.
        """
        result = self.validate_and_fix_with_report(svg)
        return result.svg

    def _extract_svg_root(self, svg: str) -> str:
        """Extract the first <svg>...</svg> block if the response is wrapped or has extra content."""
        stripped = svg.strip()
        if not stripped.lower().startswith("<svg"):
            return svg
        if stripped.rstrip().endswith("</svg>") and stripped.count("<svg") == 1 and stripped.count("</svg>") == 1:
            return svg
        # Find first <svg (start of tag)
        start_match = re.search(r"<svg\s", stripped, re.IGNORECASE)
        if not start_match:
            start_match = re.search(r"<svg>", stripped, re.IGNORECASE)
        if not start_match:
            return svg
        start = start_match.start()
        depth = 0
        i = start
        while i < len(stripped) - 4:
            sub = stripped[i : i + 5].lower()
            if sub.startswith("<svg") and (sub[4] in (">", " ", "\t", "\n")):
                depth += 1
                i += 5
                continue
            if stripped[i : i + 6].lower() == "</svg>":
                depth -= 1
                if depth == 0:
                    return stripped[start : i + 6]
                i += 6
                continue
            i += 1
        return svg

    def _validate_and_fix_tree(self, root: ET.Element) -> str | None:
        """Apply validation and fixes to the parsed tree. Returns serialized SVG or None on error."""
        try:
            self._ensure_root_attributes(root)
            self._remove_script_and_events(root)
            self._fix_animate_attributes(root)
            return self._serialize(root)
        except Exception:
            return None

    def _ensure_root_attributes(self, root: ET.Element) -> None:
        """Ensure root <svg> has required attributes for the dashboard (id, xmlns, viewBox or size)."""
        tag = _strip_ns(root.tag)
        if tag != "svg":
            return
        # Ensure xmlns
        if not root.get("xmlns"):
            root.set("xmlns", SVG_NS)
        # Ensure id="root" for dashboard iframe
        if not root.get("id"):
            root.set("id", "root")
        # Ensure viewBox or width/height for proper scaling (prefer viewBox for scaling)
        if not root.get("viewBox"):
            w = root.get("width", "960")
            h = root.get("height", "540")
            if w and h:
                root.set("viewBox", f"0 0 {w} {h}")
        # Fix invalid/negative dimensions (syntax/format)
        for attr in ("width", "height"):
            val = root.get(attr)
            if val is not None:
                try:
                    v = float(val.replace("px", "").strip())
                    if v <= 0:
                        root.set(attr, "1")
                except ValueError:
                    pass
        vb = root.get("viewBox")
        if vb:
            parts = vb.strip().split()
            if len(parts) == 4:
                try:
                    x, y, w, h = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
                    if w <= 0 or h <= 0:
                        root.set("viewBox", f"{x} {y} 960 540")
                except ValueError:
                    pass

    def _remove_script_and_events(self, el: ET.Element) -> None:
        """Remove script elements and event attributes for security."""
        # Remove <script> and handlers
        for script in list(el):
            tag = _strip_ns(script.tag).lower()
            if tag == "script":
                el.remove(script)
            else:
                self._remove_script_and_events(script)
        # Remove event attributes
        for key in list(el.attrib):
            if key.startswith("on") and len(key) > 2:
                del el.attrib[key]
            # Remove href with javascript:
            if key in ("href", f"{{{XLINK_NS}}}href"):
                val = el.attrib[key] or ""
                if "javascript:" in val.lower():
                    del el.attrib[key]

    def _fix_animate_attributes(self, el: ET.Element) -> None:
        """Fix common SMIL attribute issues (animate, animateTransform)."""
        tag = _strip_ns(el.tag).lower()
        if tag in ("animate", "animatetransform", "set"):
            # Ensure begin is a valid time (e.g. "0s" or "1.5s" or "indefinite")
            begin = el.get("begin")
            if begin is not None and "javascript:" in (begin or "").lower():
                del el.attrib["begin"]
        for child in el:
            self._fix_animate_attributes(child)

    def _serialize(self, root: ET.Element) -> str:
        """Serialize element tree back to SVG string. Avoid default_namespace to prevent
        ValueError with unqualified attributes; then normalize so output is <svg xmlns="...">.
        """
        ET.register_namespace("", SVG_NS)
        ET.register_namespace("xlink", XLINK_NS)
        out = ET.tostring(root, encoding="unicode", method="xml")
        # Normalize namespaced tags to plain <svg>, <rect>, etc. so browsers accept it
        out = re.sub(r"\{" + re.escape(SVG_NS) + r"\}(\w+)", r"\1", out)
        if "xmlns=" not in out and out.strip().startswith("<svg"):
            out = out.replace("<svg ", '<svg xmlns="' + SVG_NS + '" ', 1)
        out = _collapse_duplicate_xmlns_in_string(out)
        return out

    def _minimal_fix(self, svg: str) -> str:
        """Apply minimal regex-based fixes when full parse fails."""
        # Fix feMerge/filter tag mismatch first (can allow re-parse to succeed)
        svg = _fix_filter_femerge_mismatch(svg)
        svg = _fix_stray_femerge_close_inside_filter(svg)
        # Escape unescaped & in attribute values
        svg = _fix_unescaped_ampersands_in_attributes_simple(svg)
        # Remove <script>...</script>
        svg = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", svg, flags=re.IGNORECASE)
        # Remove on*="..." attributes
        svg = re.sub(r'\s+on\w+="[^"]*"', "", svg)
        svg = re.sub(r"\s+on\w+='[^']*'", "", svg)
        # Ensure root has id="root" if there's an <svg> without id
        if re.search(r"<svg\s+([^>]*)\s*>", svg, re.IGNORECASE):
            if 'id="root"' not in svg and "id='root'" not in svg:
                svg = re.sub(r"(<svg)(\s+)", r'\1 id="root"\2', svg, count=1, flags=re.IGNORECASE)
        svg = _collapse_duplicate_xmlns_in_string(svg)
        return svg
