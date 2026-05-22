/**
 * extract_positions.js
 *
 * Injected into the page by Playwright to extract shape descriptors
 * for every visually meaningful element on the slide.
 *
 * Two-pass algorithm:
 *   Pass 1 — Explicit tags + visual shapes (background, border, img, line)
 *   Pass 2 — Text shapes (top-down claim of block elements with text), plus
 *            direct TEXT_NODE textboxes when a host has Pass-1 descendants
 *            but only inline/paragraph element children (mixed icon + text).
 *
 * data-pptx is optional except for:
 *   "placeholder" — injects text into a template placeholder
 *   "chrome"      — skips the element and all descendants
 *
 * Returns a JSON-serialisable { meta, shapes } object.
 */

(() => {
  const STYLE_PROPS = [
    "backgroundColor",
    "color",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "textAlign",
    "whiteSpace",
    "borderColor",
    "borderWidth",
    "borderStyle",
    "borderRadius",
    "opacity",
    "flexDirection",
    "justifyContent",
    "alignItems",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
  ];

  const SKIP_TAGS = new Set([
    "STYLE", "SCRIPT", "META", "LINK", "TITLE", "HEAD", "BR", "HR",
  ]);

  const ZONE_CLASSES = new Set([
    "slide", "title", "content", "footnote", "source",
  ]);

  const BOTTOM_ZONE_TAGS = { "footnote": "footnote", "source": "source" };

  const INLINE_TAGS = new Set([
    "SPAN", "EM", "STRONG", "A", "B", "I", "SUB", "SUP", "SMALL", "MARK",
    "CODE", "ABBR", "CITE", "Q", "S", "U", "VAR", "KBD", "SAMP", "DFN",
  ]);

  const PARA_TAGS = new Set(["P", "UL", "OL", "LI"]);

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  function isZone(el) {
    for (const cls of el.classList) {
      if (ZONE_CLASSES.has(cls)) return true;
    }
    return false;
  }

  function isTransparent(color) {
    return !color || color === "transparent" || color === "rgba(0, 0, 0, 0)";
  }

  /**
   * Walk up from `el` to find the nearest grid cell ancestor (a direct
   * child of a grid/inline-grid container).  Return the content-area
   * right edge of that grid cell, or null if no grid ancestor exists.
   *
   * This lets us expand textbox widths to the available grid column
   * space instead of the browser's content-tight measurement, which
   * prevents false text wrapping in PPTX due to font-metric differences.
   */
  function findGridCellContentRight(el) {
    let current = el;
    while (current && current !== slideEl) {
      const parent = current.parentElement;
      if (!parent) break;
      const parentDisplay = getComputedStyle(parent).display;
      if (parentDisplay === "grid" || parentDisplay === "inline-grid") {
        const cellRect = current.getBoundingClientRect();
        const padR = parseFloat(getComputedStyle(current).paddingRight) || 0;
        return cellRect.right - padR;
      }
      current = parent;
    }
    return null;
  }

  function extractLineEndpoints(lineEl) {
    const svg = lineEl.closest("svg");
    if (!svg) return null;

    const svgRect = svg.getBoundingClientRect();
    const svgW = svg.viewBox?.baseVal?.width || svgRect.width;
    const svgH = svg.viewBox?.baseVal?.height || svgRect.height;
    const scaleX = svgRect.width / (svgW || 1);
    const scaleY = svgRect.height / (svgH || 1);

    const x1 = parseFloat(lineEl.getAttribute("x1") || "0");
    const y1 = parseFloat(lineEl.getAttribute("y1") || "0");
    const x2 = parseFloat(lineEl.getAttribute("x2") || "0");
    const y2 = parseFloat(lineEl.getAttribute("y2") || "0");

    const resolveX = (val, attr) => {
      const raw = lineEl.getAttribute(attr) || "0";
      return raw.endsWith("%") ? (parseFloat(raw) / 100) * svgW : val;
    };
    const resolveY = (val, attr) => {
      const raw = lineEl.getAttribute(attr) || "0";
      return raw.endsWith("%") ? (parseFloat(raw) / 100) * svgH : val;
    };

    return {
      x1: svgRect.left + resolveX(x1, "x1") * scaleX,
      y1: svgRect.top + resolveY(y1, "y1") * scaleY,
      x2: svgRect.left + resolveX(x2, "x2") * scaleX,
      y2: svgRect.top + resolveY(y2, "y2") * scaleY,
    };
  }

  function collectRuns(node, inherited, runs) {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        const text = child.textContent.replace(/[\r\n]+/g, ' ').replace(/ {2,}/g, ' ');
        if (text.trim()) {
          runs.push({ text, style: { ...inherited } });
        }
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName;
        const cs = getComputedStyle(child);
        const childStyle = {
          fontFamily: cs.fontFamily,
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          fontStyle: cs.fontStyle,
          color: cs.color,
        };
        if (tag === "SUP") childStyle.superscript = true;
        else if (tag === "SUB") childStyle.subscript = true;
        if (inherited.superscript) childStyle.superscript = true;
        if (inherited.subscript) childStyle.subscript = true;
        collectRuns(child, childStyle, runs);
      }
    }
  }

  function extractText(el) {
    if (el.tagName === "IMG") return [];
    if (el.tagName === "TABLE") return [];

    const paragraphs = [];
    const paraNodes = el.querySelectorAll("p, li");

    if (paraNodes.length > 0) {
      for (const node of paraNodes) {
        const runs = [];
        const isBullet = node.tagName === "LI"
          || node.getAttribute("data-bullet") === "true";
        const cs = getComputedStyle(node);
        collectRuns(node, {
          fontFamily: cs.fontFamily,
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          fontStyle: cs.fontStyle,
          color: cs.color,
        }, runs);
        if (runs.length > 0) {
          runs[0].text = runs[0].text.replace(/^\s+/, '');
          runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, '');
          const filtered = runs.filter(r => r.text);
          if (filtered.length > 0) {
            const para = { runs: filtered };
            if (isBullet) para.bullet = true;
            paragraphs.push(para);
          }
        }
      }
    } else {
      const runs = [];
      const cs = getComputedStyle(el);
      collectRuns(el, {
        fontFamily: cs.fontFamily,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        fontStyle: cs.fontStyle,
        color: cs.color,
      }, runs);
      if (runs.length > 0) {
        runs[0].text = runs[0].text.replace(/^\s+/, '');
        runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, '');
        const filtered = runs.filter(r => r.text);
        if (filtered.length > 0) {
          paragraphs.push({ runs: filtered });
        }
      }
    }

    return paragraphs;
  }

  function extractTable(el) {
    if (el.tagName !== "TABLE") return null;
    const rows = [];
    for (const tr of el.querySelectorAll("tr")) {
      const cells = [];
      for (const td of tr.querySelectorAll("td, th")) {
        cells.push({
          text: td.textContent.trim(),
          isHeader: td.tagName === "TH",
        });
      }
      rows.push(cells);
    }
    return rows;
  }

  function buildShape(el, tag) {
    const rect = el.getBoundingClientRect();
    const cs = getComputedStyle(el);

    const shape = {
      tag,
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      styles: {},
      data: {},
    };

    for (const prop of STYLE_PROPS) {
      shape.styles[prop] = cs[prop];
    }

    for (const attr of el.attributes) {
      if (attr.name.startsWith("data-") && attr.name !== "data-pptx") {
        shape.data[attr.name.slice(5)] = attr.value;
      }
    }

    if (tag === "line") {
      shape.line = extractLineEndpoints(el);
      shape.styles.stroke = el.getAttribute("stroke") || cs.stroke;
      shape.styles.strokeWidth = el.getAttribute("stroke-width") || cs.strokeWidth;
    } else if (tag === "image") {
      shape.src = el.getAttribute("src") || "";
      shape.alt = el.getAttribute("alt") || "";
    } else if (tag === "table") {
      shape.tableData = extractTable(el);
    } else {
      shape.text = extractText(el);
    }

    return shape;
  }

  /**
   * Union getClientRects() for a Range into one bounding box (viewport px).
   */
  function unionRangeClientRects(range) {
    const rects = range.getClientRects();
    let union = null;
    for (let i = 0; i < rects.length; i++) {
      const r = rects[i];
      if (r.width === 0 && r.height === 0) continue;
      if (!union) {
        union = { x: r.x, y: r.y, width: r.width, height: r.height };
      } else {
        const x2 = Math.max(union.x + union.width, r.x + r.width);
        const y2 = Math.max(union.y + union.height, r.y + r.height);
        union.x = Math.min(union.x, r.x);
        union.y = Math.min(union.y, r.y);
        union.width = x2 - union.x;
        union.height = y2 - union.y;
      }
    }
    return union;
  }

  /**
   * Textbox for a direct child text node under a host that fails Pass 2 Rule 6
   * (mixed inline visuals + text). Rect from Range; typography from host.
   */
  function buildTextboxFromDirectTextNode(hostEl, textNode) {
    const range = document.createRange();
    range.selectNodeContents(textNode);
    const union = unionRangeClientRects(range);
    if (!union || union.width === 0 || union.height === 0) return null;

    const cs = getComputedStyle(hostEl);
    const shape = {
      tag: "textbox",
      rect: {
        x: union.x,
        y: union.y,
        width: union.width,
        height: union.height,
      },
      styles: {},
      data: {},
    };

    for (const prop of STYLE_PROPS) {
      shape.styles[prop] = cs[prop];
    }

    for (const attr of hostEl.attributes) {
      if (attr.name.startsWith("data-") && attr.name !== "data-pptx") {
        shape.data[attr.name.slice(5)] = attr.value;
      }
    }

    const raw = textNode.textContent.replace(/[\r\n]+/g, ' ').replace(/ {2,}/g, ' ');
    const displayText = raw.trim();
    shape.text = [{
      runs: [{
        text: displayText,
        style: {
          fontFamily: cs.fontFamily,
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          fontStyle: cs.fontStyle,
          color: cs.color,
        },
      }],
    }];

    return shape;
  }

  // -----------------------------------------------------------------------
  // Pass 1 — Explicit tags + visual shapes (bg, border, img, line)
  // -----------------------------------------------------------------------

  const slideEl = document.querySelector(".slide");
  if (!slideEl) return { meta: {}, shapes: [] };

  const shapes = [];
  const pass1Set = new Set();
  const chromeSet = new Set();

  // Collect chrome elements and all their descendants first
  for (const el of slideEl.querySelectorAll('[data-pptx="chrome"]')) {
    chromeSet.add(el);
    for (const desc of el.querySelectorAll("*")) {
      chromeSet.add(desc);
    }
  }

  const allElements = slideEl.querySelectorAll("*");

  for (const el of allElements) {
    if (chromeSet.has(el)) continue;
    if (SKIP_TAGS.has(el.tagName)) continue;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    // Explicitly tagged elements — use the tag directly
    const explicitTag = el.getAttribute("data-pptx");
    if (explicitTag) {
      if (explicitTag === "chart") {
        const jsonScript = el.querySelector('script[type="application/json"]');
        if (jsonScript) {
          const shape = buildShape(el, "chart");
          try {
            shape.chartData = JSON.parse(jsonScript.textContent);
          } catch (_) { /* skip malformed JSON */ }
          shapes.push(shape);
          for (const desc of el.querySelectorAll("*")) {
            pass1Set.add(desc);
          }
        }
        pass1Set.add(el);
        continue;
      }
      shapes.push(buildShape(el, explicitTag));
      pass1Set.add(el);
      continue;
    }

    // Footnote/source zones → emit as dedicated shape tags
    for (const cls of el.classList) {
      if (BOTTOM_ZONE_TAGS[cls]) {
        const tag = BOTTOM_ZONE_TAGS[cls];
        const shape = buildShape(el, tag);
        shape.text = extractText(el);
        shapes.push(shape);
        pass1Set.add(el);
        for (const desc of el.querySelectorAll("*")) {
          pass1Set.add(desc);
        }
        break;
      }
    }
    if (pass1Set.has(el)) continue;

    // Skip zone containers for auto-detection
    if (isZone(el)) continue;

    // Skip elements inside an SVG (except <line>)
    if (el.closest("svg") && el.tagName !== "LINE") continue;

    // Auto-detect: <line> inside <svg>
    if (el.tagName === "LINE" && el.closest("svg")) {
      shapes.push(buildShape(el, "line"));
      pass1Set.add(el);
      continue;
    }

    // Auto-detect: <img>
    if (el.tagName === "IMG") {
      shapes.push(buildShape(el, "image"));
      pass1Set.add(el);
      continue;
    }

    // Auto-detect: <table>
    if (el.tagName === "TABLE") {
      shapes.push(buildShape(el, "table"));
      pass1Set.add(el);
      // Claim all descendants so cells aren't extracted as text
      for (const desc of el.querySelectorAll("*")) {
        pass1Set.add(desc);
      }
      continue;
    }

    const cs = getComputedStyle(el);
    const hasBg = !isTransparent(cs.backgroundColor);
    const borderW = parseFloat(cs.borderWidth) || 0;
    const hasBorder = borderW > 0 && !isTransparent(cs.borderColor);

    if (hasBg || hasBorder) {
      let autoTag = "rect";
      const radius = parseFloat(cs.borderRadius) || 0;
      const minDim = Math.min(rect.width, rect.height);
      if (radius >= minDim * 0.4) {
        autoTag = "ellipse";
      }
      shapes.push(buildShape(el, autoTag));
      pass1Set.add(el);
      continue;
    }
  }

  // -----------------------------------------------------------------------
  // Pass 2 — Text shapes (top-down claim)
  // -----------------------------------------------------------------------

  // Pre-claim all descendants of Pass 1 shapes so they aren't extracted again
  const claimed = new Set();
  for (const el of pass1Set) {
    for (const desc of el.querySelectorAll("*")) {
      claimed.add(desc);
    }
  }

  /** Direct text nodes already emitted as composite textboxes (Pass 2). */
  const compositeTextNodes = new Set();

  for (const el of allElements) {
    if (chromeSet.has(el)) continue;
    if (pass1Set.has(el)) continue;
    if (claimed.has(el)) continue;
    if (SKIP_TAGS.has(el.tagName)) continue;
    if (isZone(el)) continue;
    if (el.closest("svg")) continue;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;

    if (!el.textContent.trim()) continue;

    // Rule 5: all direct child ELEMENTS must be inline or paragraph-forming
    let childrenOK = true;
    for (const child of el.children) {
      if (!INLINE_TAGS.has(child.tagName) && !PARA_TAGS.has(child.tagName)) {
        childrenOK = false;
        break;
      }
    }
    if (!childrenOK) continue;

    // Grid/flex containers position paragraph children via the layout
    // algorithm — skip the container so each child becomes its own textbox.
    const elDisplay = getComputedStyle(el).display;
    if (elDisplay === 'grid' || elDisplay === 'inline-grid' ||
        elDisplay === 'flex' || elDisplay === 'inline-flex') {
      const paraChildCount = Array.from(el.children)
        .filter(c => PARA_TAGS.has(c.tagName)).length;
      if (paraChildCount > 1) continue;
    }

    // Rule 6: no descendant is a visual shape from Pass 1
    let hasDescShape = false;
    for (const desc of el.querySelectorAll("*")) {
      if (pass1Set.has(desc)) {
        hasDescShape = true;
        break;
      }
    }
    if (hasDescShape) {
      // Mixed visual + text: emit one textbox per direct TEXT_NODE (valid HTML
      // e.g. legend row = dot span + trailing label text).
      if (childrenOK) {
        for (const node of el.childNodes) {
          if (node.nodeType !== Node.TEXT_NODE) continue;
          if (!node.textContent.trim()) continue;
          if (compositeTextNodes.has(node)) continue;
          const tb = buildTextboxFromDirectTextNode(el, node);
          if (tb) {
            shapes.push(tb);
            compositeTextNodes.add(node);
          }
        }
      }
      continue;
    }

    // This element qualifies as a textbox
    const tbShape = buildShape(el, "textbox");

    // Expand width to available grid-cell space for wrapping textboxes.
    // Block elements inside flex items get content-tight widths from
    // getBoundingClientRect(); the PPTX textbox should use the full
    // column width so font-metric differences don't cause false wraps.
    const tbWs = (getComputedStyle(el).whiteSpace || "").toLowerCase();
    if (tbWs !== "nowrap" && tbWs !== "pre") {
      const gridRight = findGridCellContentRight(el);
      if (gridRight !== null) {
        const expanded = gridRight - tbShape.rect.x;
        if (expanded > tbShape.rect.width) {
          tbShape.rect.width = expanded;
        }
      }
    }

    shapes.push(tbShape);
    pass1Set.add(el);

    // Claim all descendants so they aren't extracted again
    for (const desc of el.querySelectorAll("*")) {
      claimed.add(desc);
    }
  }

  // -----------------------------------------------------------------------
  // Metadata
  // -----------------------------------------------------------------------

  const layoutEl = document.querySelector("[data-layout]");
  const meta = {
    layout: layoutEl ? layoutEl.getAttribute("data-layout") : "Default",
    viewport: { width: window.innerWidth, height: window.innerHeight },
  };

  return { meta, shapes };
})();
