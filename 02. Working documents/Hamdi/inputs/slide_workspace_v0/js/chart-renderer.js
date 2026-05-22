/**
 * chart-renderer.js
 *
 * Browser-side SVG chart renderer for the HTML-PPTX harness.
 * Reads chart definitions from `<script type="application/json">` blocks
 * inside `[data-pptx="chart"]` containers and draws an SVG preview that
 * approximates the native PowerPoint chart appearance.
 *
 * Extensible via the RENDERERS registry -- add a new chart type by
 * writing a render function and registering it in the map.
 */

(() => {
  "use strict";

  // -----------------------------------------------------------------------
  // Defaults  (McKinsey conventions: no value axis, no gridlines)
  // -----------------------------------------------------------------------

  const AXIS_LABEL_FONT_PX = 17;

  const DEFAULTS = {
    gapWidth: 150,
    dataLabels: {
      show: false,
      numberFormat: null,
      fontColor: "#FFFFFF",
      fontSize: 28,
    },
    totalLabels: {
      show: true,
      numberFormat: "0",
      fontColor: "#000000",
      fontSize: 28,
    },
    valueAxis: {
      visible: false,
      max: null,
      min: 0,
      numberFormat: null,
      gridlines: false,
    },
    categoryAxis: {
      tickMarks: false,
    },
  };

  function merge(defaults, overrides) {
    if (!overrides) return { ...defaults };
    const result = { ...defaults };
    for (const key of Object.keys(overrides)) {
      if (
        overrides[key] !== null &&
        typeof overrides[key] === "object" &&
        !Array.isArray(overrides[key]) &&
        defaults[key] &&
        typeof defaults[key] === "object"
      ) {
        result[key] = merge(defaults[key], overrides[key]);
      } else {
        result[key] = overrides[key];
      }
    }
    return result;
  }

  // -----------------------------------------------------------------------
  // SVG helpers
  // -----------------------------------------------------------------------

  const SVG_NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        el.setAttribute(k, String(v));
      }
    }
    return el;
  }

  function svgText(x, y, text, attrs) {
    const el = svgEl("text", { x, y, ...attrs });
    el.textContent = text;
    return el;
  }

  // -----------------------------------------------------------------------
  // Axis tick computation
  // -----------------------------------------------------------------------

  function niceAxisTicks(minVal, maxVal, targetCount) {
    if (maxVal === minVal) {
      return maxVal === 0 ? [0] : [0, maxVal];
    }
    const range = maxVal - minVal;
    const roughStep = range / (targetCount || 5);
    const mag = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const residual = roughStep / mag;
    let niceStep;
    if (residual <= 1.5) niceStep = 1 * mag;
    else if (residual <= 3) niceStep = 2 * mag;
    else if (residual <= 7) niceStep = 5 * mag;
    else niceStep = 10 * mag;

    const start = Math.floor(minVal / niceStep) * niceStep;
    const ticks = [];
    for (let v = start; v <= maxVal + niceStep * 0.001; v += niceStep) {
      ticks.push(Math.round(v * 1e12) / 1e12);
    }
    return ticks;
  }

  function formatValue(v, fmt) {
    if (!fmt) return String(Math.round(v * 100) / 100);
    if (fmt === "0") return String(Math.round(v));
    if (fmt === "0.0") return v.toFixed(1);
    if (fmt === "0%") return Math.round(v * 100) + "%";
    if (fmt === "0.0%") return (v * 100).toFixed(1) + "%";
    return String(v);
  }

  /** Horizontal space for end-of-bar total labels (avoids clipping wide values). */
  function estimateTotalLabelReserve(stackTotals, numberFormat, fontSize) {
    const maxVal = stackTotals.length ? Math.max(...stackTotals, 0) : 0;
    const s = formatValue(maxVal, numberFormat);
    const fs = fontSize ?? DEFAULTS.totalLabels.fontSize;
    return Math.min(
      220,
      Math.max(36, Math.ceil(s.length * fs * 0.62) + 16)
    );
  }

  /** Value scale max: align with axis ticks when axis shown; else use data/user max so bars fill the plot. */
  function valueScaleMax(valAxisVisible, axisMax, axisMin, ticks) {
    if (valAxisVisible) return ticks[ticks.length - 1];
    if (axisMax > axisMin) return axisMax;
    return ticks[ticks.length - 1] || 1;
  }

  // -----------------------------------------------------------------------
  // Renderer: bar_stacked  (horizontal stacked bars)
  // -----------------------------------------------------------------------

  function renderBarStacked(container, cfg) {
    const opts = {
      ...cfg,
      dataLabels: merge(DEFAULTS.dataLabels, cfg.dataLabels),
      totalLabels: merge(DEFAULTS.totalLabels, cfg.totalLabels),
      valueAxis: merge(DEFAULTS.valueAxis, cfg.valueAxis),
      categoryAxis: merge(DEFAULTS.categoryAxis, cfg.categoryAxis),
      gapWidth: cfg.gapWidth ?? DEFAULTS.gapWidth,
    };

    const categories = opts.categories || [];
    const series = opts.series || [];
    const catCount = categories.length;
    const multiSeries = series.length > 1;

    const stackTotals = categories.map((_, ci) =>
      series.reduce((sum, s) => sum + (s.values[ci] || 0), 0)
    );

    const w = container.clientWidth;
    const h = container.clientHeight;

    const valAxisVisible = opts.valueAxis.visible;
    const showTotalLabels = multiSeries && opts.totalLabels.show !== false;

    const valLabelHeight = valAxisVisible ? AXIS_LABEL_FONT_PX + 14 : 4;
    const totalLabelWidth = showTotalLabels
      ? estimateTotalLabelReserve(
          stackTotals,
          opts.totalLabels.numberFormat,
          opts.totalLabels.fontSize
        )
      : 0;

    const marginLeft = 6;
    const marginRight = totalLabelWidth + 10;
    const marginTop = valAxisVisible ? 4 : 0;
    const marginBottom = valAxisVisible ? valLabelHeight + 4 : 0;

    const plotW = w - marginLeft - marginRight;
    const plotH = h - marginTop - marginBottom;
    const dataMax = Math.max(...stackTotals, 0);
    const axisMin = opts.valueAxis.min ?? 0;
    const axisMax = opts.valueAxis.max ?? dataMax;
    const ticks = niceAxisTicks(axisMin, axisMax === axisMin ? axisMax + 1 : axisMax, 5);
    const scaleMax = valueScaleMax(valAxisVisible, axisMax, axisMin, ticks);

    const gapRatio = opts.gapWidth / 100;
    const totalUnits = catCount * (1 + gapRatio);
    const barH = plotH / totalUnits;
    const interGap = barH * gapRatio;
    const edgeGap = interGap / 2;

    const svg = svgEl("svg", {
      width: w,
      height: h,
      viewBox: `0 0 ${w} ${h}`,
      style: "display:block;",
    });

    // Gridlines
    if (opts.valueAxis.gridlines) {
      for (const tick of ticks) {
        const x = marginLeft + (tick / scaleMax) * plotW;
        svg.appendChild(
          svgEl("line", {
            x1: x, y1: marginTop, x2: x, y2: marginTop + plotH,
            stroke: "#D9D9D9", "stroke-width": 1,
          })
        );
      }
    }

    // Draw bars
    for (let ci = 0; ci < catCount; ci++) {
      const barY = marginTop + edgeGap + ci * (barH + interGap);
      let stackX = 0;

      for (const s of series) {
        const val = s.values[ci] || 0;
        const barW = (val / scaleMax) * plotW;
        if (barW > 0) {
          svg.appendChild(
            svgEl("rect", {
              x: marginLeft + stackX,
              y: barY,
              width: barW,
              height: barH,
              fill: s.color || "#888",
            })
          );

          if (opts.dataLabels.show && val > 0) {
            const lx = marginLeft + stackX + barW / 2;
            const ly = barY + barH / 2;
            const label = formatValue(val, opts.dataLabels.numberFormat);
            const fontSize = opts.dataLabels.fontSize;
            svg.appendChild(
              svgText(lx, ly, label, {
                fill: opts.dataLabels.fontColor || "#FFF",
                "font-size": fontSize + "px",
                "font-family": "Arial, sans-serif",
                "text-anchor": "middle",
                "dominant-baseline": "central",
              })
            );
          }

          stackX += barW;
        }
      }

      // Total label at the right end of the stacked bar
      if (showTotalLabels) {
        const total = stackTotals[ci];
        const totalX = marginLeft + stackX + 6;
        const totalY = barY + barH / 2;
        const totalFontSize = opts.totalLabels.fontSize;
        svg.appendChild(
          svgText(totalX, totalY, formatValue(total, opts.totalLabels.numberFormat), {
            fill: opts.totalLabels.fontColor || "#000000",
            "font-size": totalFontSize + "px",
            "font-family": "Arial, sans-serif",
            "text-anchor": "start",
            "dominant-baseline": "central",
          })
        );
      }
    }

    // Category axis spine at value zero (after bars so it is not covered by first segment)
    if (plotH > 0) {
      svg.appendChild(
        svgEl("line", {
          x1: marginLeft,
          y1: marginTop,
          x2: marginLeft,
          y2: marginTop + plotH,
          stroke: "#A6A6A6",
          "stroke-width": 1,
        })
      );
    }

    // Value axis line + labels
    if (valAxisVisible) {
      svg.appendChild(
        svgEl("line", {
          x1: marginLeft, y1: marginTop + plotH,
          x2: marginLeft + plotW, y2: marginTop + plotH,
          stroke: "#A6A6A6", "stroke-width": 1,
        })
      );
      for (const tick of ticks) {
        const x = marginLeft + (tick / scaleMax) * plotW;
        const label = formatValue(tick, opts.valueAxis.numberFormat);
        svg.appendChild(
          svgText(x, marginTop + plotH + AXIS_LABEL_FONT_PX + 2, label, {
            fill: "#595959",
            "font-size": AXIS_LABEL_FONT_PX + "px",
            "font-family": "Arial, sans-serif",
            "text-anchor": "middle",
          })
        );
      }
    }

    container.appendChild(svg);

    {
      const labelEl = container.parentElement?.querySelector('[data-chart-labels]');
      if (labelEl) {
        labelEl.style.position = 'relative';
        const count = Math.min(catCount, labelEl.children.length);
        for (let ci = 0; ci < count; ci++) {
          const barCenterY = marginTop + edgeGap + ci * (barH + interGap) + barH / 2;
          const child = labelEl.children[ci];
          child.style.position = 'absolute';
          child.style.top = barCenterY + 'px';
          child.style.transform = 'translateY(-50%)';
          child.style.display = 'flex';
          child.style.alignItems = 'center';
        }
      }
    }
  }

  // -----------------------------------------------------------------------
  // Renderer: column_stacked  (vertical stacked columns)
  // -----------------------------------------------------------------------

  function renderColumnStacked(container, cfg) {
    const opts = {
      ...cfg,
      dataLabels: merge(DEFAULTS.dataLabels, cfg.dataLabels),
      totalLabels: merge(DEFAULTS.totalLabels, cfg.totalLabels),
      valueAxis: merge(DEFAULTS.valueAxis, cfg.valueAxis),
      categoryAxis: merge(DEFAULTS.categoryAxis, cfg.categoryAxis),
      gapWidth: cfg.gapWidth ?? DEFAULTS.gapWidth,
    };

    const categories = opts.categories || [];
    const series = opts.series || [];
    const catCount = categories.length;
    const multiSeries = series.length > 1;

    const stackTotals = categories.map((_, ci) =>
      series.reduce((sum, s) => sum + (s.values[ci] || 0), 0)
    );

    const w = container.clientWidth;
    const h = container.clientHeight;

    const valAxisVisible = opts.valueAxis.visible;
    const showTotalLabels = multiSeries && opts.totalLabels.show !== false;

    const valLabelWidth = valAxisVisible ? 44 : 4;
    const totalFs = opts.totalLabels.fontSize;
    const totalLabelHeight = showTotalLabels
      ? Math.round(totalFs * 1.4) + 8
      : 0;

    const marginLeft = valAxisVisible ? valLabelWidth + 8 : 6;
    const marginRight = valAxisVisible ? 20 : 6;
    const marginTop = 4 + totalLabelHeight;
    const marginBottom = 4;

    const plotW = w - marginLeft - marginRight;
    const plotH = h - marginTop - marginBottom;
    const dataMax = Math.max(...stackTotals, 0);
    const axisMin = opts.valueAxis.min ?? 0;
    const axisMax = opts.valueAxis.max ?? dataMax;
    const ticks = niceAxisTicks(axisMin, axisMax === axisMin ? axisMax + 1 : axisMax, 5);
    const scaleMax = valueScaleMax(valAxisVisible, axisMax, axisMin, ticks);

    const gapRatio = opts.gapWidth / 100;
    const totalUnits = catCount * (1 + gapRatio);
    const colW = plotW / totalUnits;
    const interGap = colW * gapRatio;
    const edgeGap = interGap / 2;

    const svg = svgEl("svg", {
      width: w, height: h,
      viewBox: `0 0 ${w} ${h}`,
      style: "display:block;",
    });

    // Gridlines
    if (opts.valueAxis.gridlines) {
      for (const tick of ticks) {
        const y = marginTop + plotH - (tick / scaleMax) * plotH;
        svg.appendChild(
          svgEl("line", {
            x1: marginLeft, y1: y, x2: marginLeft + plotW, y2: y,
            stroke: "#D9D9D9", "stroke-width": 1,
          })
        );
      }
    }

    // Columns
    for (let ci = 0; ci < catCount; ci++) {
      const colX = marginLeft + edgeGap + ci * (colW + interGap);
      let stackY = 0;

      for (const s of series) {
        const val = s.values[ci] || 0;
        const colH = (val / scaleMax) * plotH;
        if (colH > 0) {
          const y = marginTop + plotH - stackY - colH;
          svg.appendChild(
            svgEl("rect", {
              x: colX, y, width: colW, height: colH,
              fill: s.color || "#888",
            })
          );

          if (opts.dataLabels.show && val > 0) {
            const lx = colX + colW / 2;
            const ly = y + colH / 2;
            const label = formatValue(val, opts.dataLabels.numberFormat);
            const fontSize = opts.dataLabels.fontSize;
            svg.appendChild(
              svgText(lx, ly, label, {
                fill: opts.dataLabels.fontColor || "#FFF",
                "font-size": fontSize + "px",
                "font-family": "Arial, sans-serif",
                "text-anchor": "middle",
                "dominant-baseline": "central",
              })
            );
          }

          stackY += colH;
        }
      }

      // Total label above the stacked column
      if (showTotalLabels) {
        const total = stackTotals[ci];
        const totalX = colX + colW / 2;
        const totalY = marginTop + plotH - stackY - 4;
        const totalFontSize = opts.totalLabels.fontSize;
        svg.appendChild(
          svgText(totalX, totalY, formatValue(total, opts.totalLabels.numberFormat), {
            fill: opts.totalLabels.fontColor || "#000000",
            "font-size": totalFontSize + "px",
            "font-family": "Arial, sans-serif",
            "text-anchor": "middle",
          })
        );
      }
    }

    // Category axis baseline (after columns so it sits on top of bar bottoms)
    if (plotW > 0) {
      svg.appendChild(
        svgEl("line", {
          x1: marginLeft,
          y1: marginTop + plotH,
          x2: marginLeft + plotW,
          y2: marginTop + plotH,
          stroke: "#A6A6A6",
          "stroke-width": 1,
        })
      );
    }

    // Value axis
    if (valAxisVisible) {
      svg.appendChild(
        svgEl("line", {
          x1: marginLeft, y1: marginTop,
          x2: marginLeft, y2: marginTop + plotH,
          stroke: "#A6A6A6", "stroke-width": 1,
        })
      );
      for (const tick of ticks) {
        const y = marginTop + plotH - (tick / scaleMax) * plotH;
        const label = formatValue(tick, opts.valueAxis.numberFormat);
        svg.appendChild(
          svgText(marginLeft - 6, y, label, {
            fill: "#595959",
            "font-size": AXIS_LABEL_FONT_PX + "px",
            "font-family": "Arial, sans-serif",
            "text-anchor": "end",
            "dominant-baseline": "central",
          })
        );
      }
    }

    container.appendChild(svg);

    {
      const labelEl = container.parentElement?.querySelector('[data-chart-labels]');
      if (labelEl) {
        labelEl.style.position = 'relative';
        const count = Math.min(catCount, labelEl.children.length);
        for (let ci = 0; ci < count; ci++) {
          const colCenterX = marginLeft + edgeGap + ci * (colW + interGap) + colW / 2;
          const child = labelEl.children[ci];
          child.style.position = 'absolute';
          child.style.left = colCenterX + 'px';
          child.style.transform = 'translateX(-50%)';
          child.style.whiteSpace = 'nowrap';
          child.style.textAlign = 'center';
        }
      }
    }
  }

  // -----------------------------------------------------------------------
  // Registry
  // -----------------------------------------------------------------------

  const RENDERERS = {
    bar_stacked: renderBarStacked,
    column_stacked: renderColumnStacked,
  };

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------

  function initCharts() {
    const containers = document.querySelectorAll('[data-pptx="chart"]');
    for (const el of containers) {
      const jsonScript = el.querySelector('script[type="application/json"]');
      if (!jsonScript) continue;

      let cfg;
      try {
        cfg = JSON.parse(jsonScript.textContent);
      } catch (e) {
        console.error("chart-renderer: invalid JSON in", el, e);
        continue;
      }

      const renderer = RENDERERS[cfg.type];
      if (!renderer) {
        console.warn("chart-renderer: unknown chart type:", cfg.type);
        continue;
      }

      renderer(el, cfg);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCharts);
  } else {
    initCharts();
  }
})();
